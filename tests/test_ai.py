"""The CAIMEx jobs beyond the talk, with the gateway replaced by fakes (no network, no cost)."""

import asyncio

import pytest

from app import ai, config, gateway, pharmacy, surveillance as sv, visits

NOW_KEEP = None


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    monkeypatch.setattr(config, "STORE", tmp_path / "sessions.json")
    monkeypatch.setattr(config, "AUDIO_DIR", tmp_path / "audio")
    visits.SESSIONS.clear(); ai.CACHE.clear(); ai.CALLS.clear()
    sv.STATE.clear(); sv.load()
    pharmacy.load()
    yield
    visits.SESSIONS.clear(); sv.STATE.clear(); pharmacy.STATE.clear(); ai.CACHE.clear()


def fake(monkeypatch, answer, fail_thinking=False):
    seen = []

    async def chat_json(step, model, system, messages, max_tokens, think=False):
        seen.append({"step": step, "think": think, "system": system, "user": messages[0]["content"]})
        if think and fail_thinking:
            raise gateway.GatewayError("504")
        out = answer(step) if callable(answer) else answer
        if isinstance(out, Exception):
            raise out
        return out, {"step": step, "model": "fake-chat", "ms": 1200, "cost": 0.0002, "thinking": think}
    monkeypatch.setattr(gateway, "chat_json", chat_json)
    return seen


PAYLOAD = {"today": [{"name": "Diarrhoea or vomiting", "expected": 9, "lo": 4, "hi": 15, "usual": 3.1}],
           "wards": [{"area": "Ward 3", "seen": 24, "usual": 2.4, "level": "confirmed"}]}


def test_the_briefing_keeps_only_text_whose_numbers_we_computed(monkeypatch):
    fake(monkeypatch, {"today": "Expect about 9 patients with diarrhoea, between 4 and 15. The usual is 3.1.",
                       "wards": "Ward 3 has 24 cases against a usual 2.4 and will reach 60 next week.",
                       "national": "", "do_first": ["Check oral rehydration salts.", "Order 500 sachets."]})
    out = asyncio.run(ai._brief(PAYLOAD))
    assert out["today"].startswith("Expect about 9") and out["wards"] == ""        # 60 was never computed
    assert out["do_first"] == ["Check oral rehydration salts."] and out["dropped"] is True
    assert ai.numbers_ok("Ward 3 saw 24 against 2.4 in the last 7 days", PAYLOAD)
    assert not ai.numbers_ok("about 31 expected", PAYLOAD)


def test_the_model_is_given_numbers_and_told_not_to_add_any(monkeypatch):
    seen = fake(monkeypatch, {"today": "Quiet.", "wards": "", "national": "", "do_first": []})
    asyncio.run(ai._brief(PAYLOAD))
    assert "Do not add, estimate" in seen[0]["system"] and '"Ward 3"' in seen[0]["user"] and seen[0]["think"] is False
    for prompt in (ai.BRIEF_SYSTEM, ai.WHY_SYSTEM, ai.DRAFT_SYSTEM):
        assert "Use ONLY the facts and numbers" in prompt


def test_while_the_model_thinks_or_fails_the_numbers_are_still_there(monkeypatch):
    async def go(answer):
        fake(monkeypatch, answer)
        first = ai.brief(PAYLOAD)
        await asyncio.gather(*ai._tasks)
        return first, ai.brief(PAYLOAD)
    first, then = asyncio.run(go({"today": "Expect about 9.", "wards": "", "national": "", "do_first": []}))
    assert first["status"] == "working" and "today" not in first
    assert then["status"] == "ready" and then["today"] == "Expect about 9."
    ai.CACHE.clear()
    first, then = asyncio.run(go(gateway.GatewayError("504")))
    assert then["status"] == "failed" and "today" not in then


def test_the_same_numbers_are_not_sent_to_the_model_twice(monkeypatch):
    async def go():
        seen = fake(monkeypatch, {"today": "ok", "wards": "", "national": "", "do_first": []})
        ai.brief(PAYLOAD); await asyncio.gather(*ai._tasks)
        ai.brief(PAYLOAD); ai.brief(PAYLOAD); await asyncio.gather(*ai._tasks)
        return len(seen)
    assert asyncio.run(go()) == 1


def test_a_drafted_text_message_fits_a_phone_and_never_says_confirmed_on_its_own(monkeypatch):
    fake(monkeypatch, {"sms": "Unusual rise in diarrhoea in Ward 3. " + "Boil water. " * 30, "note": "Ward 3 saw 24 cases."})
    out = asyncio.run(ai.draft(PAYLOAD))
    assert len(out["sms"]) <= 160 and out["note"] == "Ward 3 saw 24 cases."
    assert 'never "outbreak confirmed"' in ai.DRAFT_SYSTEM


def test_a_stalled_reasoning_call_is_tried_once_more_without_it(monkeypatch):
    seen = fake(monkeypatch, {"consider": [{"name": "Gastroenteritis", "why": "two days of diarrhoea"}]}, fail_thinking=True)
    s = visits.new("sn"); s["note"] = {"patient": "Adult", "chief_complaint": "Diarrhoea", "history": [], "red_flags": []}
    out = asyncio.run(ai.consider(s, "Diarrhoea is confirmed in Ward 3"))
    assert [c["think"] for c in seen] == [True, False] and out["consider"][0]["name"] == "Gastroenteritis"


def test_the_doctors_list_is_made_from_the_note_and_vitals_and_never_holds_a_medicine_field(monkeypatch):
    seen = fake(monkeypatch, {"consider": [{"name": "A", "why": "x"}] * 9, "do_not_miss": ["B"] * 9, "ask_or_examine": ["C"] * 9,
                              "local": "Fits", "prescribe": "amoxicillin 500 mg"})
    s = visits.new("sn"); s["note"] = {"patient": "Adult, 19", "chief_complaint": "Diarrhoea", "history": ["two days"], "red_flags": []}
    visits.set_detail(s, "bp", "95/60"); visits.set_detail(s, "area", "Ward 3")
    out = asyncio.run(ai.consider(s, "Diarrhoea is confirmed in Ward 3"))
    assert set(out) == {"key", "at", "model", "consider", "do_not_miss", "ask", "local"}
    assert (len(out["consider"]), len(out["do_not_miss"]), len(out["ask"])) == (4, 3, 4)
    assert "95/60" in seen[0]["user"] and "Ward 3" in seen[0]["user"]
    assert "do not name any medicine" in ai.CONSIDER_SYSTEM.lower()
    asyncio.run(ai.consider(s, "Diarrhoea is confirmed in Ward 3"))
    assert len(seen) == 1                                             # same note and vitals: not asked again


def test_reorder_advice_keeps_only_medicines_on_the_shelf(monkeypatch):
    fake(monkeypatch, {"summary": "Order ORS.", "orders": [{"med": "ors", "urgency": "now", "why": "diarrhoea is rising"},
                                                           {"med": "gold", "urgency": "now", "why": "x"},
                                                           {"med": "ors", "urgency": "soon", "why": "again"},
                                                           {"med": "insulin", "urgency": "tomorrow", "why": "low"}]})
    shelf = pharmacy.forecast()
    payload = {"shelf": [{"id": m["id"], "name": m["name"], "unit": m["unit"], "left": m["stock"],
                          "used_a_day": m["per_day"], "days_left_at_this_rate": m["days_left"]} for m in shelf],
               "rising_illnesses": []}
    out = asyncio.run(ai._reorder(payload))
    assert [(o["med"], o["urgency"]) for o in out["orders"]] == [("ors", "now"), ("insulin", "watch")]


def test_the_models_symptom_group_is_used_and_fixed_words_only_when_it_did_not_answer(monkeypatch):
    def visit(**extra):
        s = visits.new("sn"); s["status"] = "ready"
        s["turns"].append({"role": "user", "text": "x", "en": "I have a fever"})
        visits.set_detail(s, "area", "Ward 1")
        s.update(extra)
        return s["id"]
    a, b, c = visit(syndrome="diarrhoea"), visit(syndrome=""), visit()
    sv.STATE["events"] = []
    sv.sync(visits.SESSIONS)
    got = {e["key"]: e["syndrome"] for e in sv.STATE["events"]}
    assert got == {a: "diarrhoea", c: "fever"}                       # b: the model said "none", so it is not a case
    fake(monkeypatch, lambda step: {"group": "Breathing"})
    assert asyncio.run(ai.syndrome("cough for two days")) == "breathing"
    fake(monkeypatch, lambda step: {"group": "none"})
    assert asyncio.run(ai.syndrome("collecting tablets")) is None
