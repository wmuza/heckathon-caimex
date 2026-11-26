"""CAIMEx models beyond the patient's talk: outbreaks, stock, the doctor's page.

More jobs for the chat model, all through the CAIMEx gateway:

  brief       the chat model puts the forecast's numbers into a morning briefing
  why, draft  the chat model explains one warning, and drafts the message to send
  consider    the chat model, reasoning, lists what the doctor may want to rule out
  reorder     the chat model reads the shelf and the outbreak together
  syndrome    the chat model puts a visit into a symptom group

The models are slow and can fail (504s under load), so nothing waits on them:
each answer is fetched in the background, kept until its input changes, and the
plain arithmetic in surveillance.py and pharmacy.py is shown meanwhile and
beside it. A model's answer is never spoken to a patient, never changes an
urgency level, and never writes a prescription.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time

from . import config, gateway, surveillance

CALLS: list[dict] = []          # every call made here, for the Engine page
CACHE: dict[str, dict] = {}     # name -> {"key", "status", "result", "at", "error"}
_tasks: set[asyncio.Task] = set()

CONSIDER_SECONDS = 45
REORDER_SECONDS = 75       # 8 s on a quiet gateway, over 40 s on a busy one (both seen on 2026-11-26)
SYNDROME_SECONDS = 9


def _log(call: dict) -> None:
    CALLS.append(call)
    del CALLS[:-300]


async def _chat(step: str, system: str, payload, tokens: int, seconds: float, think: bool) -> tuple[dict, dict]:
    """One JSON answer from the chat model. With reasoning first when asked; if that stalls
    (the gateway answered 504 after two minutes on 2026-11-26), once more without it."""
    msg = [{"role": "user", "content": payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)}]
    if think:
        try:
            out, call = await asyncio.wait_for(
                gateway.chat_json(step, config.NOTE_MODEL, system, msg, tokens, think=True), seconds)
            _log(call)
            return out, call
        except Exception:
            pass
    out, call = await asyncio.wait_for(
        gateway.chat_json(step, config.NOTE_MODEL, system, msg, min(tokens, 2500), think=False), seconds)
    _log(call)
    return out, call


def _key(payload) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]


def cached(name: str, payload, make) -> dict:
    """The answer for this input if there is one; otherwise start fetching it and say so.
    `make` is an async function returning the result."""
    key = _key(payload)
    hit = CACHE.get(name)
    if hit and hit["key"] == key and (hit["status"] != "failed" or time.time() - hit["at"] < 120):
        return hit
    entry = {"key": key, "status": "working", "result": hit["result"] if hit else None,
             "stale": bool(hit and hit.get("result")), "at": time.time(), "error": None}
    CACHE[name] = entry

    async def run():
        try:
            entry["result"] = await make()
            entry["status"], entry["stale"] = "ready", False
        except Exception as e:          # the page falls back to the arithmetic
            entry["status"], entry["error"] = "failed", f"{type(e).__name__}: {e}"[:160]
        entry["at"] = time.time()

    try:
        task = asyncio.get_running_loop().create_task(run())
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)
    except RuntimeError:
        entry["status"], entry["error"] = "failed", "no event loop"
    return entry


def view(entry: dict) -> dict:
    return {"status": entry["status"], "stale": entry.get("stale", False), "at": entry["at"],
            "error": entry["error"], **(entry["result"] or {})}


# ── Explaining the predictions ──────────────────────────────────────────────
# The numbers come from app/prediction.py and app/national.py. The model is handed them and may
# only put them into words. Any number it writes that we did not give it gets its text thrown away.

GROUND = """Use ONLY the facts and numbers in the data you are given. Do not add, estimate, round \
differently or invent any number, date, place or cause. If the data does not say, do not say. Plain \
English for clinic staff: short sentences, no jargon, no statistics words. Never name a medicine \
dose. The case history in the data is made up for a demonstration; do not mention that."""

BRIEF_SYSTEM = f"""You brief the sister-in-charge of a primary care clinic in Zimbabwe before the \
doors open. You are given what a forecasting program expects today, what it has flagged in the \
clinic's wards, and the national warnings for the clinic's province. {GROUND}

Reply with one JSON object and nothing else:
{{"today": "<one or two sentences: what to expect today and how it compares with the usual>",
 "wards": "<one or two sentences on what is rising and where, most serious first; or that nothing is>",
 "national": "<one sentence on the warning for this province and what drives it; or empty>",
 "do_first": ["<one concrete thing staff can do this morning>", "<a second>", "<a third at most>"]}}"""

WHY_SYSTEM = f"""A member of clinic staff has asked why the screen shows a warning. You are given \
the numbers behind it. Explain in two or three sentences what the numbers show, which of them \
matters most, and one thing that could make the warning wrong (for example small numbers, one busy \
day, or made-up report counts). {GROUND}

Reply with one JSON object and nothing else: {{"answer": "<your explanation>"}}"""

DRAFT_SYSTEM = f"""Draft a warning for a human to check and send. You are given the numbers behind \
it. Write (1) a text message for community health workers, at most 160 characters, saying what is \
rising, where, and one thing to tell households; and (2) a short note to the district health office: \
what was seen, since when, in which ages if known, and what the clinic asks for. Say "unusual rise" \
or "likely", never "outbreak confirmed", unless the data's level is "confirmed". {GROUND}

Reply with one JSON object and nothing else: {{"sms": "<the text message>", "note": "<the note>"}}"""

ALLOWED_NUMBERS = {"1", "2", "3", "7", "14", "24", "160"}      # "one thing", "7 days", "24 hours": not data


def numbers_ok(text: str, payload) -> bool:
    """Every number in the model's words must be one we gave it."""
    import re
    given = set(re.findall(r"\d+(?:\.\d+)?", json.dumps(payload, default=str))) | ALLOWED_NUMBERS
    given |= {g.split(".")[0] for g in given} | {str(round(float(g))) for g in given if len(g) < 12}
    return all(n in given or n.rstrip("0").rstrip(".") in given for n in re.findall(r"\d+(?:\.\d+)?", text))


def _checked(out: dict, payload, keys: tuple) -> dict:
    """Keep only the text whose numbers all came from us; say so if any was dropped."""
    kept, dropped = {}, False
    for k in keys:
        v = out.get(k)
        if isinstance(v, list):
            good = [str(x)[:240] for x in v if numbers_ok(str(x), payload)]
            dropped |= len(good) != len(v)
            kept[k] = good[:3]
        else:
            v = str(v or "")[:480]
            ok = numbers_ok(v, payload)
            dropped |= not ok
            kept[k] = v if ok else ""
    kept["dropped"] = dropped
    return kept


async def _brief(payload: dict) -> dict:
    out, call = await _chat("brief", BRIEF_SYSTEM, payload, 1200, 45, think=False)
    return {**_checked(out, payload, ("today", "wards", "national", "do_first")), "model": call["model"],
            "seconds": round(call["ms"] / 1000, 1)}


def brief(payload: dict) -> dict:
    """This morning's briefing in words, fetched in the background and kept until the numbers change."""
    return view(cached("brief", payload, lambda: _brief(payload)))


async def why(payload: dict) -> dict:
    out, call = await _chat("why", WHY_SYSTEM, payload, 600, 30, think=False)
    return {**_checked(out, payload, ("answer",)), "model": call["model"]}


async def draft(payload: dict) -> dict:
    out, call = await _chat("draft", DRAFT_SYSTEM, payload, 900, 40, think=False)
    got = _checked(out, payload, ("sms", "note"))
    got["sms"] = got["sms"][:160]
    return {**got, "model": call["model"]}


# ── The doctor: things to consider ─────────────────────────────────────────

CONSIDER_SYSTEM = """You assist a doctor at a primary care clinic in Zimbabwe. You are given the \
intake note taken from a patient's own words, the measurements staff took, and what is currently \
rising in the patient's area. The doctor examines the patient and decides; you only widen what \
they think about. You have not seen the patient.

Rules:
- "consider": up to four conditions worth ruling in or out, most likely first, each with the \
finding in the note that points to it. Use common, plain names.
- "do_not_miss": up to three dangerous possibilities that must be excluded even if unlikely.
- "ask_or_examine": up to four things to ask, examine or measure that would tell the conditions apart.
- If something is rising in the patient's area and fits the complaint, say so in "local".
- Do not name any medicine, dose or treatment. Do not state a diagnosis as fact.
- Use only what you are given. If the note is thin, say less.

Reply with one JSON object and nothing else:
{"consider": [{"name": "<condition>", "why": "<the finding that points to it>"}],
 "do_not_miss": ["<condition and the sign that would suggest it>"],
 "ask_or_examine": ["<one thing>"],
 "local": "<one sentence on what is rising in their area and whether it fits, or empty>"}"""


async def consider(visit: dict, local: str) -> dict:
    """Ideas for the doctor, from the note and the vitals. Kept on the visit, with the input it was made from."""
    n, d = visit.get("note") or {}, visit.get("details") or {}
    shown = {k: (f"{v['value']} {v.get('unit') or ''}".strip() + (f" ({v['source']})" if v.get("source") else ""))
             for k, v in d.items() if v and v.get("value") is not None and k != "area"}
    payload = {"patient": n.get("patient"), "complaint": n.get("chief_complaint"), "history": n.get("history"),
               "danger_signs": n.get("red_flags"), "measurements": shown, "rising_in_their_area": local or "nothing"}
    key = _key(payload)
    old = visit.get("consider") or {}
    if old.get("key") == key:
        return old
    out, call = await _chat("consider", CONSIDER_SYSTEM, payload, 4000, CONSIDER_SECONDS, think=True)
    visit.setdefault("trace", []).append({**call, "turn": 99})
    texts = lambda v, n: [str(x)[:200] for x in (v if isinstance(v, list) else [])][:n]
    visit["consider"] = {
        "key": key, "at": time.time(), "model": call["model"],
        "consider": [{"name": str(c.get("name") or "")[:80], "why": str(c.get("why") or "")[:200]}
                     for c in (out.get("consider") or []) if isinstance(c, dict) and c.get("name")][:4],
        "do_not_miss": texts(out.get("do_not_miss"), 3), "ask": texts(out.get("ask_or_examine"), 4),
        "local": str(out.get("local") or "")[:240],
    }
    return visit["consider"]


# ── The pharmacy: what to order, read with the outbreak in mind ────────────

REORDER_SYSTEM = """You advise the pharmacy manager of a primary care clinic in Zimbabwe. You are \
given the shelf (each medicine, how many are left, how many go out a day, the days of stock left \
at that rate) and what illnesses are rising in the clinic's area. The days left assume use stays \
the same. Your job is to say where it will NOT stay the same, and what to order first.

Rules:
- A medicine that an outbreak will draw on runs out sooner than its days left say. Name the \
outbreak and the medicine, and say roughly how much sooner.
- Rank at most five medicines, most urgent first. Leave out medicines that are comfortably stocked.
- "urgency" is "now" (order today), "soon" (order this week) or "watch".
- Plain English for a pharmacy worker. No doses, no clinical advice.

Reply with one JSON object and nothing else:
{"summary": "<one or two sentences>",
 "orders": [{"med": "<the medicine id, exactly as given>", "urgency": "now|soon|watch",
             "why": "<one sentence with the numbers>"}]}"""


async def _reorder(payload: dict) -> dict:
    out, call = await _chat("reorder", REORDER_SYSTEM, payload, 2500, REORDER_SECONDS, think=False)
    ids = {m["id"]: m["name"] for m in payload["shelf"]}
    orders = []
    for o in out.get("orders") or []:
        if isinstance(o, dict) and o.get("med") in ids and o["med"] not in {x["med"] for x in orders}:
            u = str(o.get("urgency") or "watch").lower()
            orders.append({"med": o["med"], "name": ids[o["med"]], "urgency": u if u in ("now", "soon", "watch") else "watch",
                           "why": str(o.get("why") or "")[:360]})
    return {"summary": str(out.get("summary") or "")[:400], "orders": orders[:5], "model": call["model"]}


def reorder(shelf: list[dict], rising: list[dict]) -> dict:
    payload = {"shelf": [{"id": m["id"], "name": m["name"], "unit": m["unit"], "left": m["stock"],
                          "used_a_day": m["per_day"], "days_left_at_this_rate": m["days_left"]} for m in shelf],
               "rising_illnesses": rising}
    return view(cached("reorder", payload, lambda: _reorder(payload)))


# ── A visit's symptom group ────────────────────────────────────────────────

def _syndrome_system() -> str:
    groups = "\n".join(f'- "{k}": {n}' for k, n, _, _ in surveillance.SYNDROMES)
    return f"""You sort clinic visits into symptom groups for disease surveillance. You are given \
the complaint from one visit. Choose the ONE group that best fits, or "none" when the visit is not \
an infection-like illness (an injury, a refill, a check-up, pregnancy care, long-standing pain).
{groups}
- "none"
Reply with one JSON object and nothing else: {{"group": "<key>"}}"""


async def syndrome(text: str) -> str | None:
    """The symptom group of a complaint, by the chat model. Raises if the model cannot be reached."""
    out, call = await asyncio.wait_for(gateway.chat_json(
        "syndrome", config.CHAT_MODEL, _syndrome_system(), [{"role": "user", "content": text[:600]}], 60),
        SYNDROME_SECONDS)
    _log(call)
    g = str(out.get("group") or "").lower()
    return g if g in surveillance.NAME else None
