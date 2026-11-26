"""The safety claims, tested with the gateway replaced by fakes (no network, no cost)."""

import asyncio

import pytest

from app import config, gateway, prompts, triage, visits


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    monkeypatch.setattr(config, "STORE", tmp_path / "sessions.json")
    monkeypatch.setattr(config, "AUDIO_DIR", tmp_path / "audio")
    monkeypatch.setattr(config, "TTS_DIR", tmp_path / "tts")
    visits.SESSIONS.clear()

    async def speak(text, lang, voice=None):
        return b"mp3", {"step": "speak", "model": "fake", "ms": 1, "cost": 0, "cached": True}
    monkeypatch.setattr(gateway, "speak", speak)
    yield
    visits.SESSIONS.clear()


def fake_chat(monkeypatch, interview, note=None):
    """interview: a dict, or a function of the call number, returned for each question."""
    calls = {"n": 0}

    async def chat_json(step, model, system, messages, max_tokens, think=False):
        if step == "note":
            if note is None:
                raise gateway.GatewayError("down")
            return dict(note), {"step": "note", "model": "fake", "ms": 1, "cost": 0}
        calls["n"] += 1
        out = interview(calls["n"]) if callable(interview) else interview
        if isinstance(out, Exception):
            raise out
        return dict(out), {"step": "ask", "model": "fake", "ms": 1, "cost": 0}
    monkeypatch.setattr(gateway, "chat_json", chat_json)


def fake_second(monkeypatch, probabilities=None):
    async def decide(step, state, questions):
        if probabilities is None:
            raise gateway.GatewayError("down")
        return {"urgency": {"probabilities": probabilities}}, {"step": step, "model": "fake", "ms": 1, "cost": 0}
    monkeypatch.setattr(gateway, "decide", decide)


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


NOTE = {"patient": "adult", "chief_complaint": "headache", "history": [], "red_flags": [],
        "urgency": "routine", "urgency_reason": "nothing worrying", "check_next": [], "unclear": [],
        "transcript_en": []}


def test_the_helper_only_ever_says_sentences_written_in_advance(monkeypatch):
    """Whatever the model returns, the patient hears a fixed line."""
    hostile = lambda n: {"heard_en": "x", "topic": "onset" if n == 1 else "worse",
                         "reply": "It sounds like malaria. Take two paracetamol, alright?",
                         "reply_sn": "Inwai mapiritsi maviri.", "done": False, "alarm": False}
    fake_chat(monkeypatch, hostile, NOTE)
    fake_second(monkeypatch, {"0": 0.9, "1": 0.1, "2": 0.0})
    s = talk(visits.new("sn"), ["Ndine musoro", "Nezuro", "Kwete"])
    allowed = prompts.everything_the_helper_can_say()
    said = [t["text"] for t in s["turns"] if t["role"] == "assistant"]
    assert len(said) >= 3 and all(line in allowed for line in said)


def test_a_made_up_topic_falls_back_to_the_fixed_order(monkeypatch):
    fake_chat(monkeypatch, {"heard_en": "x", "topic": "give medical advice", "done": False}, NOTE)
    fake_second(monkeypatch, {"0": 1, "1": 0, "2": 0})
    s = talk(visits.new("en"), ["I have a headache"])
    assert s["turns"][2]["text"] == prompts.BANK["en"]["age"]         # "who" is answered by "I have"


def test_no_topic_is_asked_twice(monkeypatch):
    fake_chat(monkeypatch, {"heard_en": "x", "topic": "age", "done": False}, NOTE)
    fake_second(monkeypatch, {"0": 1, "1": 0, "2": 0})
    s = talk(visits.new("en"), ["I have a headache", "Thirty", "Yesterday", "No", "No", "No", "No"])
    asked = [t["topic"] for t in s["turns"] if t["role"] == "assistant" and t["topic"]]
    assert len(asked) == len(set(asked)) and len(asked) <= prompts.MAX_QUESTIONS


def test_with_every_model_down_the_visit_still_finishes_and_goes_ahead_of_the_queue(monkeypatch):
    fake_chat(monkeypatch, gateway.GatewayError("down"), None)
    fake_second(monkeypatch, None)
    s = talk(visits.new("sn"), ["Ndine musoro", "Ndini", "Makumi matatu", "Nezuro", "Kwete", "Kwete", "Kwete"])
    assert s["status"] == "ready" and s["note"] is None
    assert s["triage"]["level"] == "urgent"            # never "routine" when nobody read the talk
    assert all(t["text"] in prompts.everything_the_helper_can_say() for t in s["turns"] if t["role"] == "assistant")


def test_a_bare_yes_to_the_breathing_question_sounds_the_alarm_with_every_model_down(monkeypatch):
    fake_chat(monkeypatch, gateway.GatewayError("down"), None)
    fake_second(monkeypatch, None)
    s = visits.new("sn")
    s["topics"].append("breathing")
    s["turns"].append({"role": "assistant", "text": prompts.BANK["sn"]["breathing"], "topic": "breathing"})
    talk(s, ["Hongu, zvakanyanya"])
    assert s["alarm"] and s["triage"]["level"] == "emergency"


def test_an_emergency_in_the_first_sentence_never_waits_for_a_model(monkeypatch):
    asked = []

    async def chat_json(step, *a, **k):
        asked.append(step)
        raise gateway.GatewayError("down")
    monkeypatch.setattr(gateway, "chat_json", chat_json)
    fake_second(monkeypatch, None)
    s = visits.new("sn")
    events = []

    async def go():
        async for ev in visits.take_turn(s, text="Mwana wangu ari kutadza kufema"):
            events.append(ev)
            if ev["type"] == "reply":
                assert asked == []                    # the alarm line came before any model call
        await visits.wait_for_notes()
    asyncio.run(go())
    reply = next(e for e in events if e["type"] == "reply")
    assert reply["alarm"] and reply["done"] and reply["text"] == prompts.LINES["sn"]["alarm"]
    assert s["triage"]["level"] == "emergency"


def test_the_second_opinion_alone_can_raise_to_urgent_but_never_to_emergency(monkeypatch):
    fake_chat(monkeypatch, {"heard_en": "I have a headache", "topic": "age", "done": True}, NOTE)
    fake_second(monkeypatch, {"0": 0.0, "1": 0.01, "2": 0.99})
    s = talk(visits.new("en"), ["I have a headache"])
    assert s["triage"]["level"] == "urgent"


def test_the_checks_never_lower_what_the_rules_found(monkeypatch):
    fake_chat(monkeypatch, {"heard_en": "x", "topic": "age", "done": False}, NOTE)   # the note says routine
    fake_second(monkeypatch, {"0": 1.0, "1": 0.0, "2": 0.0})
    s = talk(visits.new("sn"), ["Mwana abatwa nepfari kaviri husiku"])
    assert s["triage"]["level"] == "emergency" and "Danger-sign rules" in s["triage"]["raised_by"]


def test_a_level_the_nurse_set_survives_the_note_arriving(monkeypatch):
    fake_chat(monkeypatch, {"heard_en": "x", "topic": "age", "done": True},
              {**NOTE, "urgency": "emergency"})
    fake_second(monkeypatch, {"0": 0, "1": 0, "2": 1})
    s = visits.new("en")

    async def go():
        async for _ in visits.take_turn(s, text="I have a headache"):
            pass
        s["triage"] = {**s["triage"], "level": "routine", "set_by_nurse": True}   # set while the note is written
        await visits.wait_for_notes()
    asyncio.run(go())
    assert s["triage"]["level"] == "routine" and s["triage"]["draft_level"] == "emergency"


def test_a_failed_note_can_be_written_again_and_the_nurses_level_stands(monkeypatch):
    fake_chat(monkeypatch, {"heard_en": "I have a headache", "topic": "age", "done": True}, None)
    fake_second(monkeypatch, None)
    s = talk(visits.new("en"), ["I have a headache"])
    assert s["status"] == "ready" and s["note"] is None and s["note_failed"] and "could not be written" in s["error"]
    assert s["triage"]["level"] == "urgent"                              # nobody read the talk: ahead of the queue

    # It fails again: it says so again, and the visit is back where it was.
    async def again():
        visits.retry_note(s)
        assert s["status"] == "summarising" and "error" not in s
        await visits.wait_for_notes()
    asyncio.run(again())
    assert s["status"] == "ready" and s["note"] is None and "could not be written" in s["error"]

    # Now the note model answers: the note is in, the message is gone, the checks are combined again.
    fake_chat(monkeypatch, {"heard_en": "x", "topic": "age", "done": True}, NOTE)
    asyncio.run(again())
    assert s["status"] == "ready" and s["note"]["chief_complaint"] == "headache"
    assert "error" not in s and not s["note_failed"] and s["triage"]["level"] == "routine"

    # A level the nurse set herself is never overwritten by a new note.
    s["note"], s["note_failed"], s["triage"] = None, True, {**s["triage"], "level": "emergency", "set_by_nurse": True}
    asyncio.run(again())
    assert s["triage"]["level"] == "emergency" and s["triage"]["draft_level"] == "routine"


def test_three_silences_hand_the_visit_to_the_nurse(monkeypatch):
    fake_chat(monkeypatch, {"heard_en": "", "topic": "age", "done": False}, None)
    fake_second(monkeypatch, None)
    s = talk(visits.new("sn"), ["", "...", " "])
    assert s["status"] == "ready" and s["triage"]["level"] == "urgent"


def test_a_one_letter_answer_is_an_answer(monkeypatch):
    fake_chat(monkeypatch, {"heard_en": "5", "topic": "onset", "done": False}, NOTE)
    fake_second(monkeypatch, {"0": 1, "1": 0, "2": 0})
    s = visits.new("en")

    async def go():
        async for _ in visits.take_turn(s, text="5"):
            pass
    asyncio.run(go())
    assert s["turns"][1]["text"] == "5" and s["turns"][2]["text"] == prompts.BANK["en"]["onset"]


def test_a_patient_who_walks_away_is_not_lost(monkeypatch):
    fake_chat(monkeypatch, {"heard_en": "x", "topic": "age", "done": False}, NOTE)
    fake_second(monkeypatch, {"0": 1, "1": 0, "2": 0})
    s = visits.new("sn")

    async def go():
        async for _ in visits.take_turn(s, text="Ndine musoro"):
            pass
        s["updated"] -= 3600
        visits.sweep()
        await visits.wait_for_notes()
    asyncio.run(go())
    assert s["status"] == "ready" and s["id"] in visits.SESSIONS


def test_old_visits_are_deleted_while_the_server_runs(monkeypatch):
    s = visits.new("sn")
    s["status"] = "seen"
    s["created"] -= (config.KEEP_HOURS + 1) * 3600
    visits.sweep()
    assert s["id"] not in visits.SESSIONS


# ── The patient's details: age from speech by fixed tables, the rest typed by staff ──

from app import details  # noqa: E402


@pytest.mark.parametrize("text,value,unit", [
    ("Ndine makore makumi matatu nemashanu", 35, "years"),
    ("makumi matatu", 30, "years"),
    ("35", 35, "years"),
    ("Ndine makore 62", 62, "years"),
    ("gumi nemaviri", 12, "years"),
    ("Ane makore matatu", 3, "years"),
    ("Mwedzi mitatu", 3, "months"),
    ("Ane mavhiki maviri", 2, "weeks"),
    ("ane gore", 1, "years"),
    ("I am thirty five", 35, "years"),
    ("She is 8 months old", 8, "months"),
    ("a 3-year-old", 3, "years"),
])
def test_age_is_read_from_the_answer(text, value, unit):
    got = details.parse_age(text, asked=True)
    assert (got["value"], got["unit"], got["source"]) == (value, unit, "said")


def test_months_never_become_years():
    assert details.parse_age("mwedzi mitatu", asked=True)["unit"] == "months"


@pytest.mark.parametrize("text", ["Handizivi", "I don't know", "makore 400", "hongu"])
def test_an_age_that_was_not_heard_is_left_empty_with_the_words(text):
    got = details.parse_age(text, asked=True)
    assert got["value"] is None and got["raw"] == text and got["flag"]


@pytest.mark.parametrize("text", [
    "Ndine musoro kubva nezuro",                         # no age at all
    "Zvakatanga mazuva matatu apfuura, ndine 65 kg",     # a number with no age unit beside it
    "Ndine makore 30, mwana ane makore matatu",          # two ages: whose is it? left for the nurse
])
def test_outside_the_age_question_only_one_clear_age_counts(text):
    assert details.parse_age(text, asked=False) is None


@pytest.mark.parametrize("text,value,unit", [
    ("Mwana wangu ane makore matatu ari kukosora", 3, "years"),
    ("Mwana ane mwedzi misere, ari kuramba zamu", 8, "months"),
    ("My son is 4 years old and has a fever", 4, "years"),
])
def test_an_age_said_in_passing_is_kept(text, value, unit):
    got = details.parse_age(text, asked=False)
    assert (got["value"], got["unit"]) == (value, unit)


def test_weight_and_height_ranges():
    assert details.entry("weight", "12.4")["value"] == 12.4
    assert details.entry("weight", "12.4")["source"] == "measured"
    assert details.entry("height", 98)["unit"] == "cm"
    for field, bad in (("weight", 0.4), ("weight", 400), ("height", 5.6), ("height", 300), ("weight", "abc")):
        with pytest.raises(details.Refused):
            details.entry(field, bad)


def test_a_heavy_child_is_flagged_to_weigh_again():
    assert details.entry("weight", 65, child=True)["flag"]
    assert details.entry("weight", 65, child=False)["flag"] is None
    assert details.entry("weight", 6.5, child=True)["flag"] is None


def test_details_never_change_the_level_or_reach_a_model():
    s = visits.new("sn")
    before = triage.combine(visits._checks(s))
    visits.set_detail(s, "weight", 3.1)
    visits.set_detail(s, "height", 50)
    visits.set_detail(s, "sex", "female")
    assert triage.combine(visits._checks(s)) == before
    assert s["details"]["weight"]["source"] == "measured"
    assert "weight" not in prompts.NOTE_SYSTEM.lower() and "height" not in prompts.interview_system("sn").lower()
    row = visits.vitals_row(s)
    assert set(row) == {"id", "number", "status", "picture", "level", "created", "child", "details", "photo", "fee"}   # no words the patient said


def test_no_name_is_kept():
    assert "name" not in details.EMPTY
    with pytest.raises(details.Refused):
        details.entry("name", "Tendai")


def test_staff_age_is_not_replaced_by_speech():
    s = visits.new("sn")
    visits.set_detail(s, "age", 4, "years")
    visits._note_age(s, "makore makumi mana", True)
    assert s["details"]["age"]["value"] == 4 and s["details"]["age"]["source"] == "entered"


def test_blood_pressure_is_typed_as_upper_over_lower():
    got = details.entry("bp", "120/80")
    assert (got["value"], got["upper"], got["lower"], got["unit"], got["source"], got["flag"]) == \
        ("120/80", 120, 80, "mmHg", "measured", None)
    for bad in ("120", "80/120", "400/80", "120/10", "12/8", "abc", "120/80/60"):
        with pytest.raises(details.Refused):
            details.entry("bp", bad)


def test_a_very_high_or_low_pressure_is_kept_with_a_warning_and_does_not_move_the_level():
    assert "Very high" in details.entry("bp", "190/100")["flag"]
    assert "Very high" in details.entry("bp", "150/125")["flag"]
    assert "Low" in details.entry("bp", "85/50")["flag"]
    s = visits.new("sn")
    before = triage.combine(visits._checks(s))
    visits.set_detail(s, "bp", "190/100")
    assert triage.combine(visits._checks(s)) == before


# ── Not asking what the patient has already said ──

@pytest.mark.parametrize("text,child,expected", [
    ("Chifuwa changu chiri kurwadza", False, {"who"}),
    ("Ndiri kunzwa musoro ne flu", False, {"who"}),
    ("I am 21 and I broke my leg just now, I cannot walk", False, {"who", "age", "onset"}),
    ("Mwana wangu ane makore matatu ari kupisa muviri kubva nezuro", False, {"who", "age", "onset"}),
    ("Zviri kuwedzera", False, {"worse"}),
    ("Hongu", False, set()),
])
def test_what_the_patients_own_words_already_answer(text, child, expected):
    assert visits.covered_by_words(text, child) == expected


def test_a_topic_the_model_marks_answered_is_never_asked(monkeypatch):
    fake_chat(monkeypatch, lambda n: {"heard_en": "x", "topic": "age" if n == 1 else "onset", "done": False,
                                      "answered": ["who", "onset", "where", "not a topic", 7]}, NOTE)
    fake_second(monkeypatch, {"0": 1, "1": 0, "2": 0})
    s = talk(visits.new("sn"), ["Gumbo rinorwadza", "Makumi maviri"])
    asked = [t["topic"] for t in s["turns"] if t["role"] == "assistant" and t["topic"]]
    assert asked[1] == "age" and "onset" not in asked and "who" not in asked and "where" not in asked
    assert set(s["covered"]) >= {"who", "onset", "where"} and "not a topic" not in s["covered"]


def test_when_the_model_is_down_the_fixed_order_still_skips_what_was_said(monkeypatch):
    fake_chat(monkeypatch, gateway.GatewayError("down"), NOTE)
    fake_second(monkeypatch, {"0": 1, "1": 0, "2": 0})
    s = talk(visits.new("en"), ["I am 23 and my chest has hurt since yesterday"])
    assert s["turns"][2]["topic"] == "worse"                          # who, age and onset were all in the first message


def test_the_model_is_told_what_is_already_answered(monkeypatch):
    seen = []

    async def chat_json(step, model, system, messages, max_tokens, think=False):
        seen.append(system)
        return ({"heard_en": "x", "topic": "fever", "done": False} if step == "ask" else dict(NOTE)), \
            {"step": step, "model": "fake", "ms": 1, "cost": 0}
    monkeypatch.setattr(gateway, "chat_json", chat_json)
    fake_second(monkeypatch, {"0": 1, "1": 0, "2": 0})
    talk(visits.new("en"), ["I am 23 and my chest has hurt since yesterday"])
    assert "Already answered in earlier messages (never ask these again): age, onset, who" in seen[0]
    assert '"answered"' in seen[0]


@pytest.mark.parametrize("lines,stops_after", [
    (["I broke my leg, I cannot walk", "I said I have just broken my leg"], 2),
    (["Ndatyoka gumbo riri kurwadza", "Yesterday", "Gumbo rangu rakatyoka riri kurwadza"], 3),
    (["My leg hurts", "No", "Since Monday", "I want to see the nurse"], 4),
])
def test_a_patient_who_repeats_themselves_is_not_asked_again(monkeypatch, lines, stops_after):
    fake_chat(monkeypatch, lambda n: {"heard_en": "", "topic": ["onset", "worse", "severity", "fever", "other"][n - 1],
                                      "done": False}, NOTE)
    fake_second(monkeypatch, {"0": 1, "1": 0, "2": 0})
    s = talk(visits.new("en"), lines + ["should never be reached"] * 3)
    assert sum(1 for t in s["turns"] if t["role"] == "user") == stops_after
    assert s["turns"][-1]["text"] == prompts.LINES["en"]["closing"] and s["stopped_early"]


def test_a_plain_yes_or_no_twice_is_not_a_repeat(monkeypatch):
    fake_chat(monkeypatch, lambda n: {"heard_en": "", "topic": ["fever", "vomiting", "worse", "onset", "other"][n - 1],
                                      "done": False}, NOTE)
    fake_second(monkeypatch, {"0": 1, "1": 0, "2": 0})
    s = talk(visits.new("en"), ["My stomach hurts", "No", "No", "No"])
    assert sum(1 for t in s["turns"] if t["role"] == "user") == 4 and not s.get("stopped_early")
