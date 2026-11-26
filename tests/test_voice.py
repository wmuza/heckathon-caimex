"""Speech outside the talk: the board, medicine instructions, the alarm and dictation. No network."""

import pytest
from fastapi.testclient import TestClient

from app import config, gateway, pharmacy, prompts, server, visits, voice


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    monkeypatch.setattr(config, "STORE", tmp_path / "sessions.json")
    monkeypatch.setattr(config, "AUDIO_DIR", tmp_path / "audio")
    monkeypatch.setattr(config, "NURSE_PIN", "")
    visits.SESSIONS.clear(); voice.CALLS.clear(); pharmacy.load()
    said = []

    async def speak(text, lang, voice=None):
        said.append((text, lang))
        return b"mp3:" + text.encode(), {"step": "speak", "model": "fake", "ms": 1, "cost": 0, "cached": True}

    async def transcribe(blob, name, mime, lang):
        return "Acute gastroenteritis.", {"step": "hear", "model": "fake-stt", "ms": 700, "cost": 0.03}
    monkeypatch.setattr(gateway, "speak", speak)
    monkeypatch.setattr(gateway, "transcribe", transcribe)
    yield said
    visits.SESSIONS.clear(); voice.CALLS.clear(); pharmacy.STATE.clear()


@pytest.mark.parametrize("n,words", [(1, "poshi"), (10, "gumi"), (14, "gumi nemana"), (20, "makumi maviri"),
                                     (35, "makumi matatu nemashanu"), (100, "zana"), (104, "zana nemana"), (250, "250")])
def test_ticket_numbers_in_shona_words(n, words):
    assert voice.shona_number(n) == words


def test_every_announcement_is_a_sentence_written_in_advance():
    assert voice.call_text("sn", "doctor", 14) == "Nhamba gumi nemana, ndapota endai kuna chiremba."
    assert voice.call_text("en", "pharmacy", 7) == "Ticket 7, please go to the pharmacy."
    assert set(prompts.CALLS["sn"]) == set(prompts.CALLS["en"]) == set(voice.PLACES)
    assert set(prompts.HOW_SAY["sn"]) == set(prompts.HOW_SAY["en"]) == set(pharmacy.HOW)
    assert voice.how_text("sn", "something a model wrote") == prompts.HOW_SAY["sn"]["As directed"]
    # none of this is in the interview, so the model never sees it and the evaluated prompt is unchanged
    assert "ndapota endai" not in prompts.interview_system("sn") and "Shandisai" not in prompts.interview_system("sn")


def test_the_patient_is_called_on_as_they_move_and_the_board_holds_only_numbers(fresh):
    s = visits.new("sn"); s["status"] = "ready"
    c = TestClient(server.app)
    assert c.post(f"/api/visits/{s['id']}/call", json={"to": "nurse"}).json()["to"] == "nurse"
    assert c.post(f"/api/visits/{s['id']}/call", json={"to": "theatre"}).status_code == 400
    c.post(f"/api/visits/{s['id']}/seen?seen=true")                                   # the nurse is done: to the doctor
    c.post(f"/api/visits/{s['id']}/consult", json={"diagnosis": "High blood pressure", "outcome": "treated",
                                                    "rx": [{"med": "amlodipine", "qty": 30, "how": "Once a day"}]})
    board = c.get("/api/board").json()
    assert [x["to"] for x in board["calls"]] == ["nurse", "doctor", "pharmacy"]
    assert all(set(x) == {"id", "at", "number", "to", "langs"} for x in board["calls"])
    assert board["calls"][0]["langs"] == ["sn", "en"]                                 # the patient's language first
    assert c.get(f"/api/board?after={board['last']}").json()["calls"] == []
    assert c.get(f"/api/board/{board['calls'][1]['id']}/sn.mp3").content == f"mp3:Nhamba {voice.shona_number(s['number'])}, ndapota endai kuna chiremba.".encode()


def test_the_board_counts_who_waits_and_shows_only_fixed_public_notices(fresh, monkeypatch):
    for status in ("ready", "summarising", "talking", "seen"):
        visits.new("sn")["status"] = status
    monkeypatch.setattr(server.national, "for_clinic", lambda now=None: [
        {"disease": "diarrhoeal", "level": "confirmed", "picture": "vomiting", "advice": "for staff", "drivers": []},
        {"disease": "malaria", "level": "watch", "picture": "fever", "advice": "for staff", "drivers": []}])
    server._NOTICES["at"] = 0
    board = TestClient(server.app).get("/api/board").json()
    assert board["waiting"] == 2                                                        # waiting for the nurse only
    assert board["notices"] == [{"disease": "diarrhoeal", "level": "confirmed", "picture": "vomiting",
                                 "sn": prompts.WARN_SAY["sn"]["diarrhoeal"], "en": prompts.WARN_SAY["en"]["diarrhoeal"]}]
    server._NOTICES["at"] = 0


def test_the_counts_are_numbers_only_and_match_each_screen(fresh, monkeypatch):
    def visit(status, level=None, **details):
        s = visits.new("sn"); s["status"] = status
        if level: s["triage"] = {"level": level}
        if details: s["details"] = {k: {"value": v} for k, v in details.items()}
        return s
    visit("ready", "emergency")                                   # waiting; straight to the nurse, not measured
    visit("ready", "urgent", weight=10, height=80, bp="100/60")   # waiting, measured
    visit("summarising")                                          # waiting, to measure
    visit("talking")                                              # still with the helper: nowhere yet
    visit("seen", "routine")                                      # seen by the nurse: the doctor's
    c = TestClient(server.app).get("/api/counts").json()
    assert c["nurse"] == 3 and c["emergency"] == 1 and c["vitals"] == 1 and c["doctor"] == 1 and c["pharmacy"] == 0
    assert set(c) == {"nurse", "emergency", "vitals", "doctor", "pharmacy", "order"}
    assert all(isinstance(v, int) for v in c.values())
    monkeypatch.setattr(config, "NURSE_PIN", "1234")
    assert TestClient(server.app).get("/api/counts").status_code == 401   # behind the staff PIN


def test_no_pharmacy_call_when_nothing_was_prescribed():
    s = visits.new("en"); s["status"] = "seen"
    TestClient(server.app).post(f"/api/visits/{s['id']}/consult", json={"diagnosis": "Headache", "outcome": "treated"})
    assert voice.CALLS == []


def test_how_to_take_it_and_the_alarm_are_fixed_words(fresh):
    c = TestClient(server.app)
    assert c.get("/api/say/how.mp3?how=Twice a day&lang=sn").content == b"mp3:" + prompts.HOW_SAY["sn"]["Twice a day"].encode()
    s = visits.new("sn"); s["alarm"] = "whatever a model wrote"
    s["live_signs"] = [{"key": "breathing", "label": "Difficulty breathing", "level": "emergency", "source": "x"}]
    assert c.get(f"/api/visits/{s['id']}/alarm.mp3").content == f"mp3:Emergency. Ticket {s['number']}. Difficulty breathing.".encode()
    assert "whatever a model wrote" not in " ".join(t for t, _ in fresh)


def test_dictation_writes_what_the_doctor_said_and_nothing_is_saved_until_the_doctor_sends():
    s = visits.new("en"); s["status"] = "seen"
    c = TestClient(server.app)
    assert c.post("/api/dictate", files={"file": ("d.wav", b"tiny", "audio/wav")}).status_code == 400
    r = c.post("/api/dictate", files={"file": ("d.wav", b"RIFF" + b"0" * 9000, "audio/wav")}, data={"lang": "en"})
    assert r.json() == {"text": "Acute gastroenteritis"} and "consult" not in s
