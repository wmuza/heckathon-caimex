"""Online visits, from home: the patient is told what fits where they are, and the clinic can call back.
The gateway is replaced by fakes (no network, no cost)."""

import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from app import config, details, gateway, prompts, server, visits, voice

PHONE = "0771234567"
NOTE = {"patient": "adult", "chief_complaint": "headache", "history": [], "red_flags": [],
        "urgency": "routine", "urgency_reason": "nothing worrying", "check_next": [], "unclear": [],
        "transcript_en": []}


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    monkeypatch.setattr(config, "STORE", tmp_path / "sessions.json")
    monkeypatch.setattr(config, "AUDIO_DIR", tmp_path / "audio")
    monkeypatch.setattr(config, "TTS_DIR", tmp_path / "tts")
    monkeypatch.setattr(config, "NURSE_PIN", "")
    visits.SESSIONS.clear(); voice.CALLS.clear(); server.ONLINE_STARTS.clear()
    sent = []                                     # everything handed to any model, to look for the phone number

    async def speak(text, lang, voice=None):
        sent.append(text)
        return b"mp3", {"step": "speak", "model": "fake", "ms": 1, "cost": 0, "cached": True}

    async def chat_json(step, model, system, messages, max_tokens, think=False):
        sent.append(json.dumps([system, messages]))
        if step == "note":
            return dict(NOTE), {"step": "note", "model": "fake", "ms": 1, "cost": 0}
        return {"heard_en": "x", "topic": "onset", "done": False}, {"step": "ask", "model": "fake", "ms": 1, "cost": 0}

    async def decide(step, state, questions):
        sent.append(json.dumps([state, questions], default=str))
        return {"urgency": {"probabilities": {"0": 1, "1": 0, "2": 0}}}, {"step": step, "model": "fake", "ms": 1, "cost": 0}
    monkeypatch.setattr(gateway, "speak", speak)
    monkeypatch.setattr(gateway, "chat_json", chat_json)
    monkeypatch.setattr(gateway, "decide", decide)
    yield sent
    visits.SESSIONS.clear(); voice.CALLS.clear(); server.ONLINE_STARTS.clear()


def talk(s, lines):
    async def go():
        for line in lines:
            if s["status"] != "talking":
                break
            async for _ in visits.take_turn(s, text=line):
                pass
        if s["status"] == "talking":
            visits.finish(s)
        await visits.wait_for_notes()
    asyncio.run(go())
    return s


def said(s):
    return [t["text"] for t in s["turns"] if t["role"] == "assistant"]


@pytest.mark.parametrize("typed", ["0771234567", "077 123 4567", "+263 77 123 4567", "263771234567", "077-123-4567"])
def test_a_mobile_number_is_kept_in_one_form(typed):
    assert details.phone(typed) == PHONE


@pytest.mark.parametrize("typed", ["", None, "077123456", "02041234567", "0242123456", "call me", "07712345678"])
def test_anything_but_a_mobile_number_is_refused(typed):
    with pytest.raises(details.Refused):
        details.phone(typed)


def test_at_home_the_helper_never_says_the_nurse_is_coming(fresh):
    s = talk(visits.new("sn", online=True, phone=PHONE), ["Mwana wangu ari kutadza kufema"])
    assert s["alarm"] and s["triage"]["level"] == "emergency"
    assert said(s)[0] == prompts.ONLINE_LINES["sn"]["greeting"]
    assert said(s)[-1] == prompts.ONLINE_LINES["sn"]["alarm"] and config.EMERGENCY_NUMBER in said(s)[-1]
    assert not any(line in (prompts.LINES["sn"]["alarm"], prompts.LINES["sn"]["closing"]) for line in said(s))


def test_at_home_a_finished_talk_says_the_clinic_will_call_back(fresh):
    s = talk(visits.new("sn", online=True, phone=PHONE), ["Ndine musoro"] + ["Kwete"] * prompts.MAX_QUESTIONS)
    assert said(s)[-1] == prompts.ONLINE_LINES["sn"]["closing"]


def test_at_the_clinic_nothing_changes(fresh):
    s = talk(visits.new("sn"), ["Mwana wangu ari kutadza kufema"])
    assert said(s)[0] == prompts.LINES["sn"]["greeting"] and said(s)[-1] == prompts.LINES["sn"]["alarm"]
    assert not s["online"] and s["phone"] is None


def test_the_phone_number_never_reaches_a_model(fresh):
    s = talk(visits.new("en", online=True, phone=PHONE), ["I have a headache", "Since yesterday", "No"])
    assert s["note"] and fresh and not any(PHONE in x or "771234567" in x for x in fresh)
    assert visits.public(s)["phone"] == PHONE                     # the nurse sees it


def test_every_online_line_is_fixed_synthesised_and_captioned():
    for lang in config.LANGS:
        for key, line in prompts.ONLINE_LINES[lang].items():
            assert line in prompts.fixed_lines(lang) and line in prompts.everything_the_helper_can_say()
            if lang != "en":
                assert prompts.english_of(lang, line) == prompts.ONLINE_LINES["en"][key]


def test_an_online_visit_needs_a_mobile_number(fresh):
    c = TestClient(server.app)
    assert c.post("/api/visits?lang=en&online=1").status_code == 400
    assert c.post("/api/visits?lang=en&online=1", data={"phone": "12345"}).status_code == 400
    r = c.post("/api/visits?lang=en&online=1", data={"phone": "077 123 4567"}).json()
    assert r["online"] and r["phone"] == PHONE and r["text"] == prompts.ONLINE_LINES["en"]["greeting"]
    assert visits.SESSIONS[r["id"]]["phone"] == PHONE


def test_online_visits_are_limited_and_clinic_visits_are_not(fresh, monkeypatch):
    c = TestClient(server.app)
    for _ in range(config.ONLINE_PER_HOUR):
        assert c.post("/api/visits?online=1", data={"phone": PHONE}).status_code == 200
    assert c.post("/api/visits?online=1", data={"phone": PHONE}).status_code == 429
    assert all(c.post("/api/visits").status_code == 200 for _ in range(5))
    server.ONLINE_STARTS.clear()
    monkeypatch.setattr(config, "ONLINE_PER_DAY", 1)
    assert c.post("/api/visits?online=1", data={"phone": PHONE}).status_code == 200
    assert c.post("/api/visits?online=1", data={"phone": PHONE}).status_code == 429   # the clinic's day is full


def test_a_patient_at_home_is_not_weighed_called_or_counted_in_the_room(fresh):
    home = visits.new("sn", online=True, phone=PHONE); home["status"] = "ready"; home["triage"] = {"level": "urgent"}
    here = visits.new("sn"); here["status"] = "ready"; here["triage"] = {"level": "urgent"}
    c = TestClient(server.app)
    assert [r["id"] for r in c.get("/api/vitals").json()["visits"]] == [here["id"]]
    assert c.get("/api/counts").json()["vitals"] == 1 and c.get("/api/counts").json()["nurse"] == 2
    assert c.get("/api/board").json()["waiting"] == 1
    assert c.post(f"/api/visits/{home['id']}/call", json={"to": "nurse"}).status_code == 409
    assert c.post(f"/api/visits/{here['id']}/call", json={"to": "nurse"}).status_code == 200


def test_the_alarm_at_the_nurses_station_says_to_call_back():
    assert "Call them back" in voice.alarm_text(12, "Chest pain", online=True)
    assert voice.alarm_text(12, "Chest pain") == "Emergency. Ticket 12. Chest pain."


def test_nothing_ever_calls_a_patient_at_home_to_a_room(fresh):
    """Marking seen and prescribing call the next room on the board by themselves. Not for someone at home."""
    from app import pharmacy
    pharmacy.load()
    home = visits.new("sn", online=True, phone=PHONE); home["status"] = "ready"; home["triage"] = {"level": "urgent"}
    c = TestClient(server.app)
    c.post(f"/api/visits/{home['id']}/seen?seen=true")                                   # nurse → doctor
    r = c.post(f"/api/visits/{home['id']}/consult", json={"diagnosis": "High blood pressure", "outcome": "treated",
                                                          "rx": [{"med": "amlodipine", "qty": 30, "how": "Once a day"}]})
    assert r.status_code == 200 and r.json()["online"] and r.json()["stage"] == "done"
    assert voice.CALLS == [] and c.get("/api/board").json()["calls"] == []
    assert next(t for t in c.get("/api/pharmacy").json()["tickets"] if t["id"] == home["id"])["online"]
    pharmacy.STATE.clear()


# ── The status page a patient at home comes back to ─────────────────────────

def _waiting_at_home(lang="en"):
    from app import pharmacy
    pharmacy.load()
    s = visits.new(lang, online=True, phone=PHONE); s["status"] = "ready"; s["triage"] = {"level": "urgent"}
    return s


def _status(c, s, digits="567"):
    return c.post(f"/api/status/{s['status_key']}", data={"digits": digits})


def test_only_online_visits_have_a_status_link_and_staff_never_see_it(fresh):
    s, here = _waiting_at_home(), visits.new("en")
    assert len(s["status_key"]) >= 20 and here["status_key"] is None
    c = TestClient(server.app)
    for url in ("/api/visits", f"/api/visits/{s['id']}", "/api/doctor", "/api/pharmacy", "/api/vitals", "/api/board"):
        assert s["status_key"] not in c.get(url).text
    r = c.post("/api/visits?lang=en&online=1", data={"phone": PHONE}).json()
    assert r["status_url"] == f"/status/{visits.SESSIONS[r['id']]['status_key']}"
    assert c.post("/api/visits?lang=en").json()["status_url"] is None
    assert c.get(r["status_url"]).status_code == 200


def test_the_status_needs_the_last_three_digits_and_locks_after_five_wrong_tries(fresh):
    s, c = _waiting_at_home(), TestClient(server.app)
    assert c.post("/api/status/not-a-real-key", data={"digits": "567"}).status_code == 404
    assert _status(c, s).status_code == 200
    for _ in range(5):
        assert _status(c, s, "000").status_code == 401
    assert _status(c, s).status_code == 429                           # locked, even with the right digits
    server.STATUS_TRIES.clear()


def test_the_status_follows_the_visit_and_gives_an_e_prescription_without_the_diagnosis(fresh):
    from app import pharmacy
    s, c = _waiting_at_home(), TestClient(server.app)
    say = prompts.STATUS_SAY["en"]
    assert _status(c, s).json()["texts"] == [say["nurse"].format(p=PHONE)]
    assert _status(c, s).json()["prescription"] is None
    c.post(f"/api/visits/{s['id']}/seen?seen=true")
    assert _status(c, s).json()["texts"] == [say["doctor"]]
    secret = "Zebra-striped secret diagnosis"
    c.post(f"/api/visits/{s['id']}/consult", json={"diagnosis": secret, "outcome": "treated",
                                                   "rx": [{"med": "amlodipine", "qty": 30, "how": "Once a day"}]})
    r = _status(c, s)
    v = r.json()
    assert v["texts"] == [say["prescription"]]
    assert v["prescription"]["number"] == s["number"] and v["prescription"]["items"] == [
        {"name": "Amlodipine 5 mg", "qty": 30, "unit": "tablets", "how": prompts.HOW_SAY["en"]["Once a day"]}]
    assert secret.lower() not in r.text.lower() and "zebra" not in r.text.lower()
    pharmacy.STATE.clear(); server.STATUS_TRIES.clear()


def test_a_patient_at_home_never_uses_the_clinic_pharmacy(fresh):
    from app import pharmacy
    s, c = _waiting_at_home(), TestClient(server.app)
    c.post(f"/api/visits/{s['id']}/consult", json={"diagnosis": "x", "outcome": "treated",
                                                   "rx": [{"med": "amlodipine", "qty": 30, "how": "Once a day"}]})
    assert pharmacy.stage(s) == "done"                                   # nothing owed here: bought elsewhere
    assert c.post("/api/pharmacy/dispense", json={"sid": s["id"], "med": "amlodipine", "qty": 30}).status_code == 409
    assert voice.CALLS == []
    pharmacy.STATE.clear()


@pytest.mark.parametrize("outcome,rx,keys", [
    ("treated", [], ["treated"]),
    ("come_in", [], ["come_in"]),
    ("come_in", [{"med": "amlodipine", "qty": 30, "how": "Once a day"}], ["come_in", "prescription"])])
def test_each_outcome_at_home_has_its_own_sentence(fresh, outcome, rx, keys):
    from app import pharmacy
    s = _waiting_at_home("sn")
    pharmacy.consult(s, "x", outcome, rx)
    assert visits.status_view(s)["texts"] == [prompts.STATUS_SAY["sn"][k].format(n=s["number"], p=PHONE) for k in keys]
    pharmacy.STATE.clear()


def test_an_emergency_at_home_keeps_the_call_for_help_on_the_status_page(fresh):
    s = _waiting_at_home(); s["alarm"] = "Difficulty breathing"
    assert visits.status_view(s)["emergency"] is True


def test_a_patient_at_home_is_treated_at_home_or_asked_to_come_in(fresh):
    from app import pharmacy
    pharmacy.load()
    here = visits.new("en"); here["status"] = "ready"
    with pytest.raises(pharmacy.Refused):
        pharmacy.consult(here, "x", "come_in", [])                      # "come to the hospital" is for home only
    for outcome in ("referred", "admitted"):
        with pytest.raises(pharmacy.Refused):
            pharmacy.consult(_waiting_at_home(), "x", outcome, [])
    for outcome in ("treated", "come_in"):
        assert pharmacy.consult(_waiting_at_home(), "x", outcome, [])["outcome"] == outcome
    pharmacy.STATE.clear()


def test_every_status_sentence_is_in_both_languages():
    assert set(prompts.STATUS_SAY["sn"]) == set(prompts.STATUS_SAY["en"])


# ── The e-prescription download, and the demo's sample ───────────────────────

def test_the_e_prescription_downloads_as_a_pdf_without_the_diagnosis(fresh):
    from app import pharmacy
    s, c = _waiting_at_home(), TestClient(server.app)
    assert c.post(f"/api/status/{s['status_key']}/prescription.pdf", data={"digits": "567"}).status_code == 404   # none yet
    c.post(f"/api/visits/{s['id']}/consult", json={"diagnosis": "Zebra secret", "outcome": "treated",
                                                   "rx": [{"med": "amlodipine", "qty": 30, "how": "Once a day"}]})
    assert c.post(f"/api/status/{s['status_key']}/prescription.pdf", data={"digits": "000"}).status_code == 401
    r = c.post(f"/api/status/{s['status_key']}/prescription.pdf", data={"digits": "567"})
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF-1.4") and r.content.rstrip().endswith(b"%%EOF")
    assert f'e-prescription-{s["number"]}.pdf' in r.headers["content-disposition"]
    assert b"Amlodipine 5 mg" in r.content and b"30 tablets" in r.content and b"SAMPLE" not in r.content
    assert b"Zebra" not in r.content
    pharmacy.STATE.clear(); server.STATUS_TRIES.clear()


def test_the_demo_sample_shows_an_e_prescription_and_is_in_no_queue(fresh):
    from app import pharmacy
    pharmacy.load()
    c = TestClient(server.app)
    assert c.get("/status/sample").status_code == 200
    v = c.post("/api/status/sample", data={"digits": "567", "lang": "sn"}).json()
    assert v["sample"] and v["lang"] == "sn" and [i["name"] for i in v["prescription"]["items"]] == \
        ["Paracetamol 500 mg", "Amoxicillin 500 mg"]
    for _ in range(6):                                                     # a demo is never locked out
        assert c.post("/api/status/sample", data={"digits": "000"}).status_code == 401
    pdf = c.post("/api/status/sample/prescription.pdf", data={"digits": "567"})
    assert pdf.status_code == 200 and b"SAMPLE - NOT A VALID PRESCRIPTION" in pdf.content
    assert "sample.pdf" in pdf.headers["content-disposition"]
    assert visits.SESSIONS == {} and c.get("/api/visits").json()["visits"] == []
    pharmacy.STATE.clear(); server.STATUS_TRIES.clear()
