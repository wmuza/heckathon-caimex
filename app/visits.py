"""A visit: the talk with the patient, the nurse's note and the four checks."""

from __future__ import annotations

import asyncio
import hmac
import json
import re
import secrets
import shutil
import time
import uuid

from . import ai, config, details, gateway, pharmacy, prompts, triage, voice

SESSIONS: dict[str, dict] = {}
_tasks: set[asyncio.Task] = set()

SCHEMA = 3          # raise this when the shape of a saved visit changes

CHILD = re.compile(r"\b(mwana|mucheche|kacheche|rusvava|child|baby|infant|son|daughter|toddler)\b", re.I)

# How long the patient is made to wait for each model before the helper moves
# on without it. A demo, or a waiting room, cannot sit through a stalled call.
HEAR_SECONDS = 25
ASK_SECONDS = 9
SPEAK_SECONDS = 12
NOTE_SECONDS = 40          # with reasoning; if that fails, once more without it
NOTE_PLAIN_SECONDS = 25
SECOND_SECONDS = 15


# ── Store ──────────────────────────────────────────────────────────────────

def save() -> None:
    config.DATA.mkdir(parents=True, exist_ok=True)
    tmp = config.STORE.with_suffix(".tmp")
    tmp.write_text(json.dumps(SESSIONS, ensure_ascii=False, indent=1))
    tmp.replace(config.STORE)


def load() -> None:
    """Read the saved visits. A visit a restart interrupted goes to the nurse as it is."""
    for d in (config.TTS_DIR, config.AUDIO_DIR):
        d.mkdir(parents=True, exist_ok=True)
    if not config.STORE.exists():
        return
    try:
        saved = json.loads(config.STORE.read_text())
    except ValueError:
        return
    for sid, s in saved.items():
        if s.get("v") != SCHEMA:        # written by an older version of this code: not readable now
            shutil.rmtree(config.AUDIO_DIR / sid, ignore_errors=True)
            continue
        if s.get("status") in ("talking", "summarising"):
            if not any(t["role"] == "user" for t in s.get("turns", [])):
                continue
            s["status"] = "ready"
            s["error"] = s.get("error") or "This visit was interrupted. Read the transcript."
            s["triage"] = triage.combine(_checks(s))
        SESSIONS[sid] = s
    purge()
    save()


def purge() -> None:
    """Delete visits older than KEEP_HOURS, recordings included."""
    cutoff = time.time() - config.KEEP_HOURS * 3600
    for sid, s in list(SESSIONS.items()):
        if s.get("created", 0) < cutoff:
            SESSIONS.pop(sid, None)
            shutil.rmtree(config.AUDIO_DIR / sid, ignore_errors=True)


def new(lang: str = "sn", sample: str | None = None, online: bool = False, phone: str | None = None) -> dict:
    """A new visit. An online one (from home) has a callback phone number, seen only by the nurse."""
    lang = lang if lang in config.LANGS else "sn"
    greeting = prompts.lines(lang, online)["greeting"]
    sid = uuid.uuid4().hex[:10]
    number = 1 + max((s.get("number", 0) for s in SESSIONS.values()), default=0)
    s = {
        "v": SCHEMA, "id": sid, "number": number, "lang": lang, "sample": sample,
        "created": time.time(), "updated": time.time(),
        "status": "talking",          # talking → summarising → ready → seen
        "online": bool(online), "phone": phone if online else None,
        # The key in the patient's status link: long and random, and not the id the staff screens use.
        "status_key": secrets.token_urlsafe(16) if online else None,
        "turns": [{"role": "assistant", "text": greeting, "topic": "main",
                   "en": prompts.english_of(lang, greeting)}],
        "questions": 1, "topics": ["main"], "child": False, "repeats": 0,
        "covered": [],                      # topics the patient has already answered, asked or not
        "alarm": None, "alarm_by": None, "live_signs": [], "answer_signs": [],
        "note": None, "triage": None, "error": None, "trace": [],
        "details": dict(details.EMPTY),     # age, sex, weight, height: beside the note, never in a model's prompt
    }
    SESSIONS[sid] = s
    return s


def remove(sid: str) -> None:
    SESSIONS.pop(sid, None)
    shutil.rmtree(config.AUDIO_DIR / sid, ignore_errors=True)
    save()


def clear() -> None:
    for sid in list(SESSIONS):
        shutil.rmtree(config.AUDIO_DIR / sid, ignore_errors=True)
    SESSIONS.clear()
    save()


def sweep(idle_minutes: float = 10) -> None:
    """A patient who walked away mid-talk must not be lost: after ten quiet
    minutes the visit goes to the nurse with whatever was said. Old visits
    are deleted here too, so the promise about recordings holds while the
    server runs, not only when it starts."""
    cutoff = time.time() - idle_minutes * 60
    for sid, s in list(SESSIONS.items()):
        if s["status"] == "talking" and s["updated"] < cutoff:
            if any(t["role"] == "user" for t in s["turns"]):
                s["error"] = s["error"] or "The patient stopped answering. Read the transcript."
                finish(s)
            else:
                remove(sid)
    before = len(SESSIONS)
    purge()
    if len(SESSIONS) != before:
        save()


def _trace(s: dict, call: dict) -> None:
    call["turn"] = sum(1 for t in s["turns"] if t["role"] == "user")
    s["trace"].append(call)


# ── The talk ───────────────────────────────────────────────────────────────

def bank_question(s: dict, topic: str) -> str:
    """The fixed sentence for a topic. This is the only way a question is worded."""
    bank = prompts.BANK[s["lang"]]
    if s["child"] and f"{topic}_child" in bank:
        return bank[f"{topic}_child"]
    return bank[topic]


def next_topic(s: dict, wanted: object) -> str | None:
    """The topic to ask about: the model's choice if it is a real topic that has
    not been asked, otherwise the next in the fixed order, otherwise nothing."""
    wanted = str(wanted or "").strip().lower()
    known = set(s["topics"]) | set(s.get("covered", []))
    if wanted in prompts.ASKABLE and wanted not in known:
        return wanted
    for topic in prompts.FALLBACK_ORDER:
        if topic not in known:
            return topic
    return None


# What a patient's own words already answer, read without the model. It is used when the model
# does not answer, and beside it, so the helper never asks "who is unwell?" after "my chest hurts".
SELF = re.compile(r"\b(ndiri|ndine|ndini|ndava|ndaka\w*|ndinorwar\w*|\w+ (yangu|rangu|wangu|changu|dzangu|angu)|i am|i'm|i have|i feel|my \w+|me)\b", re.I)
ONSET = re.compile(r"\b(nezuro|nhasi|mangwanani|manheru|usiku|izvezvi|zuro|mazuva|svondo|vhiki|mwedzi|kubva|since|yesterday|today|"
                   r"this morning|last night|just now|days?|weeks?|months?|ago)\b", re.I)
WORSE = re.compile(r"\b(\w*wedzer\w*|\w*nyanyis\w*|worse|worsening|getting bad)\b", re.I)
AGAIN = re.compile(r"\b(ndati|ndambotaura|ndataura kare|ndakuudzai|i said|i (have )?already|i told you|as i said)\b", re.I)
SEE_NOW = re.compile(r"\b(ndoda kuona (mukoti|nurse|chiremba|doctor)|(want|need) to (see|be seen)|cannot wait|handigoni kumirira)\b", re.I)


def covered_by_words(text: str, child: bool) -> set[str]:
    out = set()
    if child or CHILD.search(text) or SELF.search(text):
        out.add("who")
    if details.parse_age(text, asked=False):
        out.add("age")
    if ONSET.search(text):
        out.add("onset")
    if WORSE.search(text):
        out.add("worse")
    return out


def _same(a: str, b: str) -> bool:
    """Is one patient line much the same as another? (They are repeating themselves.)"""
    wa, wb = set(re.findall(r"\w{3,}", a.lower())), set(re.findall(r"\w{3,}", b.lower()))
    return len(wa) >= 2 and len(wb) >= 2 and len(wa & wb) / min(len(wa), len(wb)) >= 0.75


def fed_up(s: dict, heard: str, en: str | None) -> bool:
    """The patient is repeating an earlier answer or says they have already told us: stop asking.
    The first message is never counted, and a short "yes" or "no" is never a repeat."""
    earlier = [t for t in s["turns"][:-1] if t["role"] == "user"]
    if not earlier:
        return False
    for now in filter(None, (heard, en)):
        if AGAIN.search(now) or (SEE_NOW.search(now) and len(earlier) >= 2):
            return True
        if any(_same(now, t.get("en") or t["text"]) or _same(now, t["text"]) for t in earlier):
            return True
    return False


def _patient_texts(s: dict) -> list[tuple[str, str]]:
    out = []
    for t in s["turns"]:
        if t["role"] == "user":
            out.append((t["text"], s["lang"]))
            if t.get("en"):
                out.append((t["en"], "en"))
    return out


def _note_signs(s: dict) -> list[tuple[str, str]]:
    return [(f, "en") for f in (s.get("note") or {}).get("red_flags", [])]


def _sign(rule: triage.Rule) -> dict:
    return {"key": rule.key, "label": rule.label, "level": rule.level,
            "source": triage.SOURCES.get(rule.source, rule.source)}


def _all_signs(s: dict) -> list[triage.Rule]:
    """Every danger sign the rules find: in what was said, in yes/no answers
    to danger questions, and in the note's own list."""
    found = {r.key: r for r in triage.scan_all(_patient_texts(s) + _note_signs(s))}
    for key in s.get("answer_signs", []):
        if key in triage.BY_KEY:
            found.setdefault(key, triage.BY_KEY[key])
    return sorted(found.values(), key=lambda r: -triage.rank(r.level))


def _note_age(s: dict, text: str, asked: bool) -> None:
    """Keep the age the patient said, read by the fixed number tables (no model).
    A value a member of staff typed is never replaced, and an answer to the age
    question outranks an age mentioned in passing."""
    d = s.setdefault("details", dict(details.EMPTY))
    old = d.get("age") or {}
    if old.get("source") == "entered":
        return
    got = details.parse_age(text, asked)
    if not got:
        return
    if old.get("value") is not None and (got["value"] is None or old.get("asked") or not asked):
        return                                      # the first clear number stands, in the patient's own words
    d["age"] = {**got, "asked": asked}


def set_detail(s: dict, field: str, value, unit: str | None = None, source: str = "measured") -> dict:
    """A member of staff enters, corrects or clears one detail. Raises details.Refused."""
    d = s.setdefault("details", dict(details.EMPTY))
    d[field] = details.entry(field, value, unit, source, child=details.is_child(d, s.get("child", False)))
    if field == "age" and d.get("weight"):          # the age changed: look at the weight warning again
        w = d["weight"]
        w["flag"] = details.entry("weight", w["value"], child=details.is_child(d, s.get("child", False)))["flag"]
    if field == "bp" and s.get("triage") and s.get("status") != "talking":     # the reading can raise the level
        _set_triage(s, {**triage.combine(_checks(s, s.get("second"))),
                        "provisional": s.get("status") == "summarising"})
    s["updated"] = time.time()
    save()
    return d


def photo_path(s: dict):
    return config.AUDIO_DIR / s["id"] / "photo.jpg"      # beside the recordings, so it is deleted with them


def photo_url(s: dict) -> str | None:
    p = photo_path(s)
    return f"/api/visits/{s['id']}/photo?v={int(p.stat().st_mtime)}" if p.exists() else None


def vitals_row(s: dict) -> dict:
    """A visit as the vitals page sees it: the ticket and its picture, with no words the patient said."""
    return {"id": s["id"], "number": s["number"], "status": s["status"], "picture": picture_for(s),
            "level": (s.get("triage") or {}).get("level"), "created": s["created"],
            "child": details.is_child(s.get("details") or {}, s.get("child", False)),
            "photo": photo_url(s), "fee": s.get("fee"),
            "details": {**details.EMPTY, **(s.get("details") or {})}}


async def _say(s: dict, text: str, lang: str) -> bytes | None:
    try:
        mp3, call = await asyncio.wait_for(gateway.speak(text, lang), SPEAK_SECONDS)
        _trace(s, call)
        return mp3
    except Exception:
        return None


async def take_turn(s: dict, *, text: str | None = None, blob: bytes | None = None,
                    mime: str = "audio/wav", want_audio: bool = True):
    """One patient turn. Yields events: heard, reply, audio, timing."""
    lang = s["lang"]
    lines = prompts.lines(lang, s.get("online", False))
    asked = s["topics"][-1]                 # the topic of the question being answered
    t0 = time.time()

    clip = None
    if blob:
        ext = "wav" if "wav" in mime else "mp3" if "mpeg" in mime or "mp3" in mime \
            else "mp4" if "mp4" in mime else "ogg" if "ogg" in mime else "webm"
        clip = f"{len(s['turns']):02d}.{ext}"
        (config.AUDIO_DIR / s["id"]).mkdir(parents=True, exist_ok=True)
        (config.AUDIO_DIR / s["id"] / clip).write_bytes(blob)
        heard, call = await asyncio.wait_for(
            gateway.transcribe(blob, f"turn.{ext}", mime.split(";")[0], lang), HEAR_SECONDS)
        _trace(s, call)
    else:
        heard = (text or "").strip()
    t_heard = time.time()

    if not re.search(r"\w", heard):
        s["repeats"] = s.get("repeats", 0) + 1
        if s["repeats"] < 3:
            yield {"type": "heard", "text": ""}
            yield {"type": "reply", "text": lines["repeat"], "en": prompts.english_of(lang, lines["repeat"]),
                   "topic": asked, "repeat": True, "done": False, "alarm": False,
                   "question": s["questions"], "of": prompts.MAX_QUESTIONS}
            if want_audio:
                yield {"type": "audio", "mp3": await _say(s, lines["repeat"], lang)}
            return
        heard = "(nothing could be heard)"      # three silences: hand over to the nurse
    s["repeats"] = 0

    turn = {"role": "user", "text": heard, "audio": clip, "en": heard if lang == "en" else None}
    s["turns"].append(turn)
    s["updated"] = time.time()
    if CHILD.search(heard):
        s["child"] = True
    _note_age(s, heard, asked == "age")
    covered = s.setdefault("covered", [])
    covered.extend(t for t in sorted(covered_by_words(heard, s["child"])) if t not in covered)
    yield {"type": "heard", "text": heard}

    # Check 1: the rules read every patient line the moment it is written down,
    # and the question it answers ("Hongu" to "are you struggling to breathe?").
    hits = triage.scan(heard, lang)
    answered = triage.answer_sign(asked, heard)
    if answered and answered.key not in {h.key for h in hits}:
        hits.append(answered)
        s["answer_signs"].append(answered.key)
    rule_alarm = next((r for r in hits if r.level == "emergency"), None)

    out: dict = {}
    model_failed = False
    if not rule_alarm:
        try:
            out, call = await asyncio.wait_for(gateway.chat_json(
                "ask", config.CHAT_MODEL, prompts.interview_system(lang, heard, tuple(covered)),
                [{"role": t["role"], "content": t["text"]} for t in s["turns"]], 500), ASK_SECONDS)
            _trace(s, call)
        except Exception:       # slow, down or unreadable: the fixed questions take over
            out, model_failed = {}, True
        # What the model says the patient has already answered is never asked, by it or by the fixed order.
        told = out.get("answered")
        covered.extend(t for t in (told if isinstance(told, list) else [])
                       if isinstance(t, str) and t in prompts.ASKABLE and t not in covered)
        en = str(out.get("heard_en") or "").strip()
        if en and lang != "en":
            turn["en"] = en
            _note_age(s, en, asked == "age")       # the number may be clearer in the English
            covered.extend(t for t in sorted(covered_by_words(en, s["child"])) if t not in covered)
            if CHILD.search(en):
                s["child"] = True
            # The rules also read the English version, so a sign said in a way
            # the Shona patterns do not know is still caught.
            for r in triage.scan(en, "en"):
                if r.key not in {h.key for h in hits}:
                    hits.append(r)
            rule_alarm = next((r for r in hits if r.level == "emergency"), None)

    for r in hits:
        if r.key not in {x["key"] for x in s["live_signs"]}:
            s["live_signs"].append(_sign(r))

    # Check 2: the interview model can raise the alarm too.
    model_alarm = out.get("alarm") is True and not rule_alarm
    alarm = bool(rule_alarm) or model_alarm
    weary = fed_up(s, heard, turn.get("en"))
    if weary:
        s["stopped_early"] = "The patient was repeating themselves or asked to be seen, so the helper stopped asking."
    done = alarm or weary or out.get("done") is True or s["questions"] >= prompts.MAX_QUESTIONS \
        or heard == "(nothing could be heard)"
    topic = None
    if alarm:
        s["alarm"] = rule_alarm.label if rule_alarm else (
            str(out.get("alarm_reason_en") or "").strip()[:200] or "Danger sign reported")
        s["alarm_by"] = "rules" if rule_alarm else "interview"
        reply = lines["alarm"]
    else:
        if not done:
            topic = next_topic(s, out.get("topic"))
            done = topic is None
        if done:
            topic, reply = None, lines["closing"]
        else:
            # The only place a question is worded: the fixed sentence for the topic.
            reply = bank_question(s, topic)
            s["questions"] += 1
            s["topics"].append(topic)
    if model_failed and not s["error"]:
        s["error"] = "The chat model did not answer in time, so the helper asked its fixed questions."
    reply_en = prompts.english_of(lang, reply)
    s["turns"].append({"role": "assistant", "text": reply, "en": reply_en, "topic": topic})
    t_asked = time.time()

    if done:
        finish(s)
    else:
        save()
    yield {"type": "reply", "text": reply, "en": reply_en, "heard_en": turn.get("en"),
           "topic": topic or "other", "done": done, "alarm": alarm,
           "question": s["questions"], "of": prompts.MAX_QUESTIONS, **help_at_home(s)}

    if want_audio:
        yield {"type": "audio", "mp3": await _say(s, reply, lang)}
    if rule_alarm and not turn.get("en"):
        # The rules stopped the talk before the model was asked, so the patient's
        # words have no English yet. Get it now, for the nurse and the captions.
        try:
            got, call = await asyncio.wait_for(gateway.chat_json(
                "ask", config.CHAT_MODEL, prompts.interview_system(lang, heard),
                [{"role": t["role"], "content": t["text"]} for t in s["turns"][:-1]], 300), ASK_SECONDS)
            _trace(s, call)
            turn["en"] = str(got.get("heard_en") or "").strip() or None
            save()
            if turn["en"]:
                yield {"type": "gloss", "heard_en": turn["en"]}
        except Exception:
            pass
    yield {"type": "timing", "hear": round(t_heard - t0, 2), "ask": round(t_asked - t_heard, 2),
           "speak": round(time.time() - t_asked, 2)}


# ── After the talk ─────────────────────────────────────────────────────────

def _checks(s: dict, second: dict | None = None) -> list[triage.Check]:
    hits = _all_signs(s)
    note = s.get("note")
    talking = s.get("status") in ("talking", "summarising") and not s.get("note_failed")
    note_level = str((note or {}).get("urgency") or "").lower()
    if note and note_level in triage.LEVELS:
        note_check = triage.Check("Note model", note_level, str(note.get("urgency_reason") or ""),
                                  {"kind": "model", "model": config.NOTE_MODEL})
    elif talking:
        note_check = triage.Check("Note model", None, "The note is being written",
                                  {"kind": "model", "model": config.NOTE_MODEL})
    else:
        # No note: nobody has read the whole talk, so the visit goes ahead of the queue.
        note_check = triage.Check("Note model", "urgent",
                                  "The note could not be written, so this visit is put ahead of the queue",
                                  {"kind": "model", "model": config.NOTE_MODEL})
    checks = [
        triage.Check(
            "Danger-sign rules", triage.highest([r.level for r in hits]),
            ", ".join(r.label for r in hits) or "No danger sign in the patient's words",
            {"signs": [_sign(r) for r in hits], "kind": "rules"}),
        triage.Check(
            "Interview model", "emergency" if s.get("alarm_by") == "interview" else None,
            s["alarm"] if s.get("alarm_by") == "interview"
            else "Not asked: the rules stopped the talk first" if s.get("alarm_by") == "rules"
            else "Raised no alarm during the talk",
            {"kind": "model", "model": config.CHAT_MODEL}),
        note_check,
    ]
    vitals, why = details.vitals_level(s.get("details") or {})
    if vitals:          # only once a blood pressure is entered
        checks.append(triage.Check("Measured vitals", vitals, why, {"kind": "rules"}))
    if second is not None:
        checks.append(triage.Check(
            "Second opinion", second.get("level"), second.get("detail", ""),
            {"kind": "model", "model": config.DECISION_MODEL,
             "probabilities": second.get("probabilities")}))
    return checks


def _set_triage(s: dict, result: dict) -> None:
    """Store the checks' verdict without ever overwriting the nurse's own level."""
    old = s.get("triage") or {}
    if old.get("set_by_nurse"):
        result = {**result, "draft_level": result["level"], "level": old["level"], "set_by_nurse": True}
    s["triage"] = result


def finish(s: dict) -> None:
    """End the talk. The rules' verdict shows at once; the note follows."""
    s["status"] = "summarising"
    s["updated"] = time.time()
    s["talk_seconds"] = round(time.time() - s["created"])
    _set_triage(s, {**triage.combine(_checks(s)), "provisional": True})
    save()
    try:
        task = asyncio.get_running_loop().create_task(summarise(s))
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)
    except RuntimeError:        # no loop: the caller runs summarise() itself
        pass


async def summarise(s: dict) -> None:
    """Write the nurse's note, ask for the second opinion, combine the checks."""
    await _write_note(s)
    await _conclude(s)
    # For the outbreak watch: which symptom group is this visit? Asked of the model after the
    # nurse already has her note, so it never delays her. If it fails, fixed words are used instead.
    if not s.get("sample"):
        said = " ".join(t.get("en") or t["text"] for t in s["turns"] if t["role"] == "user")
        try:
            s["syndrome"] = await ai.syndrome(((s.get("note") or {}).get("chief_complaint") or "") + ". " + said) or ""
            save()
        except Exception:
            pass


def retry_note(s: dict) -> None:
    """The nurse asks for a failed note to be written again. The visit keeps its place in the queue and
    its level until the new note is in; then the checks are combined again, and the nurse's own level,
    if she set one, still stands. If it fails again, the visit says so again."""
    s["status"] = "summarising"
    s["note_failed"] = False
    s.pop("error", None)
    s["updated"] = time.time()
    save()
    try:
        task = asyncio.get_running_loop().create_task(_rewrite_note(s))
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)
    except RuntimeError:        # no loop: the caller runs _rewrite_note() itself
        pass


async def _rewrite_note(s: dict) -> None:
    await _write_note(s)
    await _conclude(s)


async def _write_note(s: dict) -> None:
    """Ask the note model for the nurse's note. If it cannot be had, say why; the transcript stays."""
    lines = "\n".join(("Helper: " if t["role"] == "assistant" else "Patient: ") + t["text"]
                      for t in s["turns"])
    try:
        try:
            note, call = await asyncio.wait_for(gateway.chat_json(
                "note", config.NOTE_MODEL, prompts.NOTE_SYSTEM,
                [{"role": "user", "content": lines}], 4000, think=True), NOTE_SECONDS)
        except Exception:
            # The reasoning call is the one that stalls when the gateway is busy
            # (504s and 502s on 2026-11-25). A plain note beats no note.
            note, call = await asyncio.wait_for(gateway.chat_json(
                "note", config.NOTE_MODEL, prompts.NOTE_SYSTEM,
                [{"role": "user", "content": lines}], 1500, think=False), NOTE_PLAIN_SECONDS)
        _trace(s, call)
        for k in ("history", "red_flags", "check_next", "unclear", "transcript_en"):
            v = note.get(k)
            note[k] = [str(x) for x in v] if isinstance(v, list) else ([] if not v else [str(v)])
        for k in ("patient", "chief_complaint", "urgency", "urgency_reason"):
            note[k] = str(note.get(k) or "")
        s["note"] = note
    except Exception as e:  # the nurse must still see the visit, with the transcript
        reason = "it took too long" if isinstance(e, asyncio.TimeoutError) else str(e)[:120]
        s["error"] = f"The note could not be written ({reason}). Read the transcript."
        s["note"] = None
        s["note_failed"] = True


async def _conclude(s: dict) -> None:
    """After the note (or its failure): the second opinion, then every check combined."""
    others = triage.combine(_checks(s))["level"]
    second = await _second_opinion(s, others)
    s["second"] = second            # kept, so a later blood pressure can re-combine the checks
    s["status"] = "ready"
    _set_triage(s, triage.combine(_checks(s, second)))
    s["updated"] = time.time()
    save()


async def _second_opinion(s: dict, others: str) -> dict:
    """Check 4: a different, smaller model reads the English note cold.

    It can move a routine visit ahead of the queue, and no more. A small
    model on its own never sounds the emergency alarm: that takes the rules,
    the interview model or the note model.
    """
    note = s["note"]
    if note:
        state = (f"Patient: {note['patient']}. Complaint: {note['chief_complaint']}. "
                 f"History: {'; '.join(note['history'])}. "
                 f"Danger signs reported: {'; '.join(note['red_flags']) or 'none'}.")
    else:
        said = [t.get("en") or t["text"] for t in s["turns"] if t["role"] == "user"]
        state = "The patient said: " + " ".join(said)
    try:
        answers, call = await asyncio.wait_for(
            gateway.decide("second_opinion", state, prompts.SECOND_OPINION), SECOND_SECONDS)
        _trace(s, call)
        probs = (answers.get("urgency") or {}).get("probabilities") or {}
        level = triage.second_opinion_level(probs, config.SECOND_OPINION_RAISE_AT)
        p = {k: round(float(probs.get(str(i), 0)), 3) for i, k in enumerate(triage.LEVELS)}
        detail = ", ".join(f"{k} {round(v * 100)}%" for k, v in p.items())
        if level == "emergency" and others != "emergency":
            level = "urgent"
            detail += ". Counted as urgent: this check alone cannot sound the alarm"
        return {"level": level, "probabilities": p, "detail": detail}
    except Exception:
        return {"level": None, "probabilities": None, "detail": "The second model did not answer"}


def placed_ahead(s: dict) -> int:
    """How many patients who arrived earlier, and are still waiting, this visit sits above."""
    mine = triage.rank((s.get("triage") or {}).get("level", "routine"))
    if s["status"] not in ("summarising", "ready"):
        return 0
    return sum(1 for o in SESSIONS.values()
               if o is not s and o["status"] in ("summarising", "ready") and o["created"] < s["created"]
               and triage.rank((o.get("triage") or {}).get("level", "routine")) < mine)


# Which picture stands for a visit in the nurse's queue: the same pictures the patient saw.
SIGN_PICTURE = {
    "breathing": "breathing", "convulsions": "fits", "cannot_drink": "drinking", "bleeding": "bleeding",
    "bleeding_yes": "bleeding", "blood": "bleeding", "pregnancy_bleeding": "pregnancy",
    "stiff_neck_fever": "neck", "stiff_neck": "neck", "chest_pain": "where", "injury": "where",
    "young_baby": "who", "poison": "medicines",
}
WORD_PICTURE = [
    (r"breath|kufema", "breathing"), (r"\bfit|convuls|seiz|pfari", "fits"), (r"pregnan|pamuviri", "pregnancy"),
    (r"tablet|pill|medic|refill|prescri|inject|immunis|mapiritsi", "medicines"),
    (r"bleed|blood(?! pressure| sugar| test)|ropa", "bleeding"), (r"vomit|rutsa", "vomiting"), (r"neck|mutsipa", "neck"),
    (r"fever|temperature|\bhot\b|kupisa", "fever"),
    (r"drink|breastfe|yamwa", "drinking"), (r"pain|ache|hurt|sore|broken|burn|wound|rwadz", "where"),
    (r"child|baby|infant|mwana", "who"),
]


def picture_for(s: dict) -> str:
    for sign in sorted(s.get("live_signs", []), key=lambda x: -triage.rank(x["level"])):
        if sign["key"] in SIGN_PICTURE:
            return SIGN_PICTURE[sign["key"]]
    note = s.get("note") or {}
    said = " ".join(t.get("en") or t["text"] for t in s["turns"] if t["role"] == "user")
    text = (note.get("chief_complaint") or said).lower()
    for pattern, name in WORD_PICTURE:
        if re.search(pattern, text):
            return name
    return "other"


SAMPLE_STATUS_KEY = "sample"


def sample_online_visit(lang: str = "en") -> dict:
    """A made-up patient at home with an e-prescription, for the demo's /status/sample (digits 567).
    Built fresh each time and never stored, so it is in no queue, no count and no pharmacy record."""
    return {"id": "sample", "number": 12, "lang": lang if lang in config.LANGS else "en", "status": "seen",
            "online": True, "phone": "0771234567", "sample": True, "alarm": None,
            "consult": {"diagnosis": "(never shown)", "outcome": "treated", "at": time.time(), "suggested": False,
                        "rx": [{"med": "paracetamol", "qty": 20, "how": "When needed"},
                               {"med": "amoxicillin", "qty": 15, "how": "Three times a day"}]}}


def by_status_key(key: str, lang: str = "en") -> dict | None:
    """The online visit a status link belongs to, or None. "sample" is the demo's made-up patient."""
    if key == SAMPLE_STATUS_KEY:
        return sample_online_visit(lang)
    for s in SESSIONS.values():
        if s.get("status_key") and hmac.compare_digest(s["status_key"].encode(), (key or "").encode()):
            return s
    return None


def help_at_home(s: dict) -> dict:
    """For a patient at home with a danger sign: first-aid steps for that sign and word that the nurse will
    call. Fixed sentences only. Empty for a clinic visit, where the nurse is coming."""
    if not (s.get("online") and s.get("alarm")):
        return {}
    sign = next((x["key"] for x in s.get("live_signs", []) if x["level"] == "emergency"), None)
    return {"first_aid": prompts.first_aid(s["lang"], sign),
            "nurse_calls": prompts.NURSE_WILL_CALL[s["lang"]].format(p=s.get("phone") or "")}


def status_view(s: dict) -> dict:
    """What a patient at home sees of their own visit: one fixed sentence for where it is and, once the
    doctor has decided, the e-prescription to show at any pharmacy. Never the diagnosis, the note or a
    model's words."""
    lang = s["lang"]
    say = prompts.STATUS_SAY[lang]
    fill = lambda key: say[key].format(n=s["number"], p=s.get("phone") or "")
    consult = s.get("consult")
    texts, rx = [], None
    if not consult:
        stage = "doctor" if s["status"] == "seen" else "nurse"
        texts.append(fill(stage))
    else:
        stage = consult["outcome"]
        if stage == "come_in" or not consult["rx"]:
            texts.append(fill(stage))
        if consult["rx"]:
            texts.append(fill("prescription"))
            meds = {m["id"]: m for m in pharmacy.STATE.get("medicines", [])}
            rx = {"date": consult["at"], "number": s["number"],
                  "items": [{"name": meds.get(l["med"], {}).get("name", l["med"]), "qty": l["qty"],
                             "unit": meds.get(l["med"], {}).get("unit", ""), "how": voice.how_text(lang, l["how"])}
                            for l in consult["rx"]]}
    return {"lang": lang, "number": s["number"], "stage": stage, "texts": texts, "prescription": rx,
            "emergency": bool(s.get("alarm")), "sample": bool(s.get("sample")),
            "first_aid": help_at_home(s).get("first_aid", [])}


def public(s: dict, full: bool = True) -> dict:
    """A visit as the nurse's screen sees it."""
    out = {k: s.get(k) for k in ("id", "number", "lang", "sample", "created", "updated", "status",
                                  "alarm", "alarm_by", "live_signs", "note", "triage", "error",
                                  "talk_seconds", "online", "phone")}
    out["turns"] = [
        {"role": t["role"], "text": t["text"], "en": t.get("en"),
         "topic": t.get("topic"),
         "audio": f"/api/visits/{s['id']}/audio/{t['audio']}" if t.get("audio") else None}
        for t in s["turns"]
    ]
    out["cost"] = round(sum(c.get("cost") or 0 for c in s["trace"]), 6)
    out["placed_ahead"] = placed_ahead(s)
    out["picture"] = picture_for(s)
    out["details"] = {**details.EMPTY, **(s.get("details") or {})}
    out["photo"] = photo_url(s)
    out["fee"] = s.get("fee")
    out["consult"] = s.get("consult")
    if full:
        out["trace"] = s["trace"]
    return out


async def wait_for_notes() -> None:
    """Let every note that is being written finish (used by tools and tests)."""
    while _tasks:
        await asyncio.gather(*list(_tasks), return_exceptions=True)
