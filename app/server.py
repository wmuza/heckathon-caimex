"""Mukoti: a voice intake line for clinics, in Shona and English.

The patient speaks. Each turn runs speech-to-text, one chat call that chooses
the next question, and text-to-speech, all through the CAIMEx gateway on models
hosted in Zimbabwe. When the talk ends, a second chat call writes the nurse's
note in English, a small decision model gives a second opinion, and the fixed
rules in triage.py can raise the urgency. Only the nurse can lower it.

Run:  uv run uvicorn app.server:app --port 8000
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import re
import statistics
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import ai, config, details, gateway, metrics, national, pharmacy, prediction, surveillance, voice, prompts, samples, triage, visits
from .gateway import GatewayError

CATALOGUE: dict[str, dict] = {}


async def _prewarm() -> None:
    """Make every fixed line once, so Mukoti never waits to say one."""
    sem = asyncio.Semaphore(3)

    async def one(text, lang, voice=None):
        async with sem:
            try:
                await gateway.speak(text, lang, voice)
            except Exception:
                pass

    jobs = [one(t, lang) for lang in config.LANGS for t in prompts.fixed_lines(lang)]
    jobs += [one(t, lang) for t, lang in voice.staff_lines()]
    try:        # the morning briefing is long: make its audio now, so the first press does not wait
        jobs.append(one(voice.briefing_text(_prediction(), national.for_clinic()), "en"))
    except Exception:
        pass
    for p in samples.all_patients():
        if p.get("demo"):
            topics = ["main", *samples.data()["defaults"][p["lang"]].keys()]
            jobs += [one(samples.line(p, t), p["lang"], p.get("voice")) for t in dict.fromkeys(topics)]
    await asyncio.gather(*jobs)


async def _load_catalogue() -> None:
    await gateway.load_prices()
    try:
        for m in await gateway.catalogue():
            CATALOGUE[m["id"]] = m
    except Exception:
        pass


async def _sweep() -> None:
    while True:
        await asyncio.sleep(60)
        try:
            surveillance.sync(visits.SESSIONS)      # before old visits are deleted, keep their nameless tally
            visits.sweep()
        except Exception:
            pass


@asynccontextmanager
async def lifespan(_: FastAPI):
    gateway.start()
    visits.load()
    pharmacy.load()
    surveillance.load()
    tasks = [asyncio.create_task(national.refresh()), asyncio.create_task(gateway.keep_warm()), asyncio.create_task(_prewarm()),
             asyncio.create_task(_load_catalogue()), asyncio.create_task(_sweep())]
    yield
    for t in tasks:
        t.cancel()
    await gateway.stop()


app = FastAPI(title="Mukoti", lifespan=lifespan)


# ── The nurse's PIN (only when MUKOTI_NURSE_PIN is set) ────────────────────

def _token() -> str:
    return hmac.new(config.API_KEY.encode(), config.NURSE_PIN.encode(), hashlib.sha256).hexdigest()[:40]


def _same(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8", "replace"), b.encode("utf-8", "replace"))


def nurse(request: Request) -> None:
    if config.NURSE_PIN and not _same(request.cookies.get("mukoti_nurse", ""), _token()):
        raise HTTPException(401, "Enter the nurse's PIN")


WRONG_PINS: list[float] = []        # times of recent wrong tries, across everyone


@app.post("/api/nurse/login")
async def nurse_login(response: Response, pin: str = Form(...)):
    now = time.time()
    WRONG_PINS[:] = [t for t in WRONG_PINS if now - t < 300]
    if len(WRONG_PINS) >= 8:
        raise HTTPException(429, "Too many wrong tries. Wait five minutes.")
    if not config.NURSE_PIN or not _same(pin, config.NURSE_PIN):
        WRONG_PINS.append(now)
        await asyncio.sleep(1)
        raise HTTPException(401, "That PIN is not right")
    response.set_cookie("mukoti_nurse", _token(), httponly=True, samesite="strict", max_age=12 * 3600)
    return {"ok": True}


# ── The patient's side ─────────────────────────────────────────────────────

def _visit(sid: str) -> dict:
    s = visits.SESSIONS.get(sid)
    if not s:
        raise HTTPException(404, "No such visit")
    return s


def _b64(data: bytes | None) -> str | None:
    return base64.b64encode(data).decode() if data else None


@app.get("/api/config")
async def get_config():
    return {"languages": [{"code": c, "name": prompts.LANG_NAME[c]} for c in config.LANGS],
            "max_questions": prompts.MAX_QUESTIONS, "pin_required": bool(config.NURSE_PIN)}


@app.post("/api/visits")
async def start_visit(lang: str = "sn", sample: str | None = None):
    if sample and not samples.get(sample):
        raise HTTPException(404, "No such sample patient")
    s = visits.new(lang, sample=sample)
    visits.save()
    text = prompts.LINES[s["lang"]]["greeting"]
    try:
        mp3, _ = await gateway.speak(text, s["lang"])
    except GatewayError:
        mp3 = None
    shown = prompts.GREETING_SHOWN[s["lang"]]
    return {"id": s["id"], "number": s["number"], "lang": s["lang"], "text": text, "show": shown,
            "en": None if s["lang"] == "en" else prompts.GREETING_SHOWN["en"], "audio": _b64(mp3),
            "question": 1, "of": prompts.MAX_QUESTIONS}


@app.post("/api/visits/{sid}/turn")
async def turn(sid: str, audio: UploadFile | None = File(None), text: str | None = Form(None)):
    """One patient turn. Streams JSON lines: heard, reply, audio, timing (or error)."""
    s = _visit(sid)
    if s["status"] != "talking":
        raise HTTPException(409, "This visit has finished")
    blob = await audio.read() if audio is not None else None
    mime = (audio.content_type if audio is not None else None) or "audio/webm"

    async def run():
        try:
            async for ev in visits.take_turn(s, text=text, blob=blob, mime=mime):
                if ev["type"] == "audio":
                    ev = {"type": "audio", "b64": _b64(ev["mp3"])}
                yield (json.dumps(ev, ensure_ascii=False) + "\n").encode()
        except Exception as e:
            visits.save()
            yield (json.dumps({"type": "error", "message": str(e)[:300]}) + "\n").encode()

    return StreamingResponse(run(), media_type="application/x-ndjson")


@app.post("/api/visits/{sid}/end")
async def end_visit(sid: str):
    """The patient or a helper ends the talk early."""
    s = _visit(sid)
    if s["status"] == "talking":
        if any(t["role"] == "user" for t in s["turns"]):
            visits.finish(s)
        else:
            visits.remove(sid)
    return {"ok": True}


# ── Sample patients (made-up, synthetic voices) ────────────────────────────

@app.get("/api/samples")
async def list_samples():
    return {"about": samples.data()["about"],
            "samples": [{k: p[k] for k in ("id", "title", "about", "lang", "expect")}
                        for p in samples.all_patients() if p.get("demo")]}


@app.get("/api/samples/{sample_id}/line")
async def sample_line(sample_id: str, topic: str = "main"):
    p = samples.get(sample_id)
    if not p:
        raise HTTPException(404, "No such sample patient")
    topic = topic if topic in prompts.TOPICS else "other"
    try:
        mp3 = await samples.voice(p, topic)
    except GatewayError as e:
        raise HTTPException(502, str(e)[:200])
    return {"text": samples.line(p, topic), "audio": _b64(mp3)}


def _issues() -> list[dict]:
    """The rows of CAIMEX_ISSUES.md."""
    try:
        text = (config.ROOT / "CAIMEX_ISSUES.md").read_text()
    except OSError:
        return []
    rows = []
    for line in text.splitlines():
        m = re.match(r"^\| (\d+) \| (.+?) \| (.+?) \| (.+?) \|$", line)
        if m:
            rows.append({"n": int(m[1]), "area": m[2], "what": m[3], "workaround": m[4]})
    return rows


@app.post("/api/demo/fill", dependencies=[Depends(nurse)])
async def fill_queue():
    """Put the demonstration patients in the queue (typed, not spoken, so it is quick)."""
    async def go():
        sem = asyncio.Semaphore(3)

        async def one(p):
            async with sem:
                try:
                    await samples.run(p)
                except Exception:
                    pass
        await asyncio.gather(*(one(p) for p in samples.all_patients() if p.get("demo")))

    asyncio.get_running_loop().create_task(go())
    return {"ok": True}


# ── The nurse's side ───────────────────────────────────────────────────────

@app.get("/api/visits", dependencies=[Depends(nurse)])
async def queue():
    order = {"emergency": 0, "urgent": 1, "routine": 2}

    def key(s):
        # Waiting patients first, most urgent first; then those still speaking; then those seen.
        group = {"talking": 1, "seen": 2}.get(s["status"], 0)
        level = order.get((s.get("triage") or {}).get("level", "routine"), 2)
        return (group, level if group == 0 else 0, s["created"])

    return {"visits": [visits.public(s, full=False) for s in sorted(visits.SESSIONS.values(), key=key)],
            "now": time.time()}


@app.get("/api/visits/{sid}", dependencies=[Depends(nurse)])
async def visit(sid: str):
    return visits.public(_visit(sid))


@app.post("/api/visits/{sid}/seen", dependencies=[Depends(nurse)])
async def mark_seen(sid: str, seen: bool = True):
    s = _visit(sid)
    if s["status"] in ("ready", "seen"):
        if seen and s["status"] == "ready" and not s.get("consult"):
            voice.call(s, "doctor")                 # the nurse has finished: the board calls the patient on
        s["status"] = "seen" if seen else "ready"
        s["updated"] = time.time()
        visits.save()
    return visits.public(s)


@app.post("/api/visits/{sid}/level", dependencies=[Depends(nurse)])
async def set_level(sid: str, level: str):
    """The nurse's own level replaces the draft, up or down. It is recorded as hers."""
    s = _visit(sid)
    if level not in triage.LEVELS:
        raise HTTPException(400, "Unknown level")
    t = s.get("triage") or triage.combine([])
    s["triage"] = {**t, "draft_level": t.get("draft_level", t.get("level")), "level": level,
                   "set_by_nurse": True, "provisional": False}
    s["updated"] = time.time()
    visits.save()
    return visits.public(s)


class Detail(BaseModel):
    field: str
    value: float | str | None = None
    unit: str | None = None
    source: str = "measured"


@app.post("/api/visits/{sid}/details", dependencies=[Depends(nurse)])
async def set_detail(sid: str, body: Detail):
    """Staff enter a detail against the ticket: sex, a measured weight or height, a corrected age.
    The patient's side has no way to call this, and no model reads what is stored."""
    s = _visit(sid)
    try:
        visits.set_detail(s, body.field, body.value, body.unit, body.source)
    except details.Refused as e:
        raise HTTPException(400, str(e))
    return visits.vitals_row(s)


# ── A photo on the ticket ──────────────────────────────────────────────────

@app.post("/api/visits/{sid}/photo", dependencies=[Depends(nurse)])
async def set_photo(sid: str, file: UploadFile = File(...)):
    """Staff attach one small photo to the ticket, so a person collecting twice can be seen.
    It is kept beside the recordings and deleted with them. No face is compared by a machine."""
    s = _visit(sid)
    blob = await file.read()
    if not blob.startswith(b"\xff\xd8") or len(blob) > 400_000:
        raise HTTPException(400, "The photo must be a JPEG under 400 KB")
    path = visits.photo_path(s)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(blob)
    s["updated"] = time.time()
    visits.save()
    return visits.vitals_row(s)


@app.delete("/api/visits/{sid}/photo", dependencies=[Depends(nurse)])
async def remove_photo(sid: str):
    s = _visit(sid)
    visits.photo_path(s).unlink(missing_ok=True)
    s["updated"] = time.time()
    visits.save()
    return visits.vitals_row(s)


@app.get("/api/visits/{sid}/photo", dependencies=[Depends(nurse)])
async def get_photo(sid: str):
    path = visits.photo_path(_visit(sid))
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=3600"})


# ── Pharmacy, fees and the supervisor's approvals ──────────────────────────

def _refuse(e: pharmacy.Refused):
    """A refusal that the supervisor can lift answers 403, so the page asks for the PIN."""
    if isinstance(e, pharmacy.NeedsSupervisor):
        now = time.time()
        WRONG_PINS[:] = [t for t in WRONG_PINS if now - t < 300]
        if len(WRONG_PINS) >= 8:
            raise HTTPException(429, "Too many wrong tries. Wait five minutes.")
        WRONG_PINS.append(now)
        raise HTTPException(403, str(e))
    raise HTTPException(400, str(e))


class Supply(BaseModel):
    sid: str
    med: str
    qty: int | str
    pin: str | None = None
    reason: str | None = None


class Consult(BaseModel):
    diagnosis: str
    outcome: str = "treated"
    rx: list[dict] = []
    suggested: bool = False


class Count(BaseModel):
    med: str
    counted: int | str
    pin: str | None = None
    reason: str | None = None


class Fee(BaseModel):
    status: str
    pin: str | None = None
    reason: str | None = None


def _today() -> float:
    return time.mktime(time.localtime()[:3] + (0, 0, 0, 0, 0, -1))


@app.get("/api/pharmacy", dependencies=[Depends(nurse)])
async def pharmacy_state():
    since = _today()
    tickets = []
    for s in sorted(visits.SESSIONS.values(), key=lambda s: s["number"]):
        if s["status"] == "talking":
            continue
        tickets.append({"id": s["id"], "number": s["number"], "photo": visits.photo_url(s), "fee": s.get("fee"),
                        "lang": s["lang"],
                        "picture": visits.picture_for(s), "stage": pharmacy.stage(s),
                        "consult": s.get("consult"),
                        "owed": {l["med"]: pharmacy.remaining(s, l["med"]) for l in (s.get("consult") or {}).get("rx", [])},
                        "given": [{"med": r["med"], "qty": -r["qty"], "at": r["at"]} for r in pharmacy.given(s["id"])]})
    shelf = pharmacy.forecast()
    return {"medicines": shelf, "tickets": tickets, "approvals": pharmacy.approvals(since),
            "advice": ai.reorder(shelf, _rising()),
            "reasons": pharmacy.WAIVER_REASONS, "rate_days": pharmacy.RATE_DAYS,
            "soon_days": pharmacy.ORDER_SOON_DAYS, "now_days": pharmacy.ORDER_NOW_DAYS,
            "demo_history": any(r.get("demo") for r in pharmacy.STATE["log"]),
            "demo_pin": config.SUPERVISOR_PIN_IS_DEMO, "now": time.time()}


@app.post("/api/pharmacy/dispense", dependencies=[Depends(nurse)])
async def pharmacy_dispense(body: Supply):
    s = _visit(body.sid)
    try:
        return pharmacy.dispense(s["id"], s["number"], body.med, body.qty, body.pin, body.reason,
                                 allowed=pharmacy.remaining(s, body.med),
                                 diagnosis=(s.get("consult") or {}).get("diagnosis"))
    except pharmacy.Refused as e:
        _refuse(e)


# ── Speech outside the talk: the board, medicine instructions, alarms, dictation ──

class Call(BaseModel):
    to: str


async def _mp3(text: str, lang: str) -> Response:
    try:
        mp3, _ = await asyncio.wait_for(gateway.speak(text, lang), 25)
    except Exception as e:
        raise HTTPException(502, f"The voice did not answer ({type(e).__name__})")
    return Response(mp3, media_type="audio/mpeg", headers={"Cache-Control": "private, max-age=3600"})


@app.post("/api/visits/{sid}/call", dependencies=[Depends(nurse)])
async def call_ticket(sid: str, body: Call):
    """Call a ticket to the nurse, the doctor or the pharmacy on the waiting-room board."""
    if body.to not in voice.PLACES:
        raise HTTPException(400, "Unknown place")
    return voice.call(_visit(sid), body.to)


_NOTICES: dict = {"at": 0.0, "list": []}


def _board_notices() -> list[dict]:
    """Health notices for the room: the fixed public sentence for each illness at high risk, or with an
    outbreak reported, in this clinic's province. Worked out at most once a minute."""
    if time.time() - _NOTICES["at"] > 60:
        try:
            ws = [w for w in national.for_clinic() if w["level"] in ("confirmed", "likely")]
        except Exception:
            ws = []
        _NOTICES.update(at=time.time(), list=[{"disease": w["disease"], "level": w["level"], "picture": w["picture"],
                                               **{lang: voice.warn_text(lang, w["disease"]) for lang in config.LANGS}} for w in ws])
    return _NOTICES["list"]


@app.get("/api/board")
async def board(after: int = 0):
    """The waiting-room board. Open to the room: ticket numbers and where to go, how many are waiting,
    and the province's public health notices. Nothing about any one patient."""
    return {"calls": [{k: c[k] for k in ("id", "at", "number", "to", "langs")} for c in voice.CALLS if c["id"] > after][-12:],
            "last": voice.CALLS[-1]["id"] if voice.CALLS else 0, "now": time.time(),
            "waiting": sum(1 for s in visits.SESSIONS.values() if s["status"] in ("summarising", "ready")),
            "notices": _board_notices()}


@app.get("/api/board/{call_id}/{lang}.mp3")
async def board_audio(call_id: int, lang: str):
    c = next((c for c in voice.CALLS if c["id"] == call_id), None)
    if not c or lang not in config.LANGS:
        raise HTTPException(404)
    return await _mp3(voice.call_text(lang, c["to"], c["number"]), lang)


@app.get("/api/say/how.mp3", dependencies=[Depends(nurse)])
async def say_how(how: str, lang: str = "sn"):
    """How to take a medicine: one of five sentences written in advance."""
    lang = lang if lang in config.LANGS else "sn"
    return await _mp3(voice.how_text(lang, how), lang)


@app.get("/api/visits/{sid}/alarm.mp3", dependencies=[Depends(nurse)])
async def alarm_audio(sid: str):
    """The emergency, said aloud at the nurse's station. The sign is a fixed label, not a model's words."""
    s = _visit(sid)
    sign = next((x["label"] for x in s.get("live_signs", []) if x["level"] == "emergency"), "Danger sign reported")
    return await _mp3(voice.alarm_text(s["number"], sign), "en")


@app.post("/api/dictate", dependencies=[Depends(nurse)])
async def dictate(file: UploadFile = File(...), lang: str = Form("en")):
    """The doctor says the diagnosis; the recogniser writes it down for the doctor to check."""
    blob = await file.read()
    if not 2000 < len(blob) <= 2_000_000:
        raise HTTPException(400, "Hold the button and speak for up to a minute")
    try:
        text, call = await asyncio.wait_for(
            gateway.transcribe(blob, "dictation.wav", "audio/wav", lang if lang in config.LANGS else "en"), 30)
    except Exception as e:
        raise HTTPException(502, f"The recogniser did not answer ({type(e).__name__})")
    ai._log({**call, "step": "dictate"})
    return {"text": text.strip().rstrip(".")}


# ── Prediction: this clinic and the country ────────────────────────────────

def _evaluation() -> dict | None:
    try:
        r = json.loads((config.EVAL / "prediction_results.json").read_text())
        return {k: r[k] for k in ("ran_at", "clinics", "settings", "detection_test", "forecast_test")}
    except (OSError, ValueError, KeyError):
        return None


def _prediction() -> dict:
    surveillance.sync(visits.SESSIONS)
    return prediction.predict(shelf=pharmacy.forecast())


def _brief_payload(pred: dict, warnings: list[dict]) -> dict:
    """What the chat model is given to put into words: computed numbers only."""
    return {"weekday": pred["weekday"],
            "expected_today": [{k: t[k] for k in ("name", "expected", "lo", "hi", "usual", "above")} for t in pred["today"]],
            "flagged_in_the_wards": [{"area": s["area"], "illness": s["name"], "level": s["level"], "seen_in_7_days": s["seen"],
                                      "usual_in_7_days": s["usual"], "expected_next_7_days": s["next7"]["mean"],
                                      "range_next_7_days": [s["next7"]["lo"], s["next7"]["hi"]],
                                      "mostly_aged": (s["age"] or {}).get("band"), "diagnosed_by_doctor": s["diagnosed"]}
                                     for s in pred["signals"]],
            "national_warnings_for_this_province": [{"illness": w["name"], "level": w["level"], "risk_out_of_100": w["score"],
                                                     "main_reasons": [f"{d['label']}: {d['value']}" for d in w["drivers"][:2]]}
                                                    for w in warnings]}


@app.get("/api/outbreaks", dependencies=[Depends(nurse)])
async def outbreaks():
    """Today's forecast, the wards, and the warnings for this province. Numbers by arithmetic;
    the words beside them by CAIMEx, from those numbers."""
    pred, warnings = _prediction(), national.for_clinic()
    return {**pred, "all_areas": surveillance.AREAS, "national": warnings, "province": config.PROVINCE,
            "brief": ai.brief(_brief_payload(pred, warnings)), "evaluation": _evaluation()}


@app.get("/api/national", dependencies=[Depends(nurse)])
async def national_picture():
    asyncio.get_running_loop().create_task(national.refresh())       # never waits for the weather service
    return national.picture()


class Ask(BaseModel):
    area: str | None = None
    syndrome: str | None = None
    province: str | None = None
    disease: str | None = None


def _evidence(q: Ask) -> dict:
    if q.province:
        w = next((w for w in national.picture()["warnings"] if w["province"] == q.province and w["disease"] == q.disease), None)
        if not w:
            raise HTTPException(404, "No warning there")
        return {"where": w["province"], "illness": w["name"], "level": w["level"], "risk_out_of_100": w["score"],
                "reasons": [{"what": d["label"], "value": d["value"], "points": d["points"], "of": d["max"],
                             "from": d["source"]} for d in w["drivers"]]}
    s = next((s for s in _prediction()["signals"] if s["area"] == q.area and s["syndrome"] == q.syndrome), None)
    if not s:
        raise HTTPException(404, "No signal there")
    return {"where": s["area"], "illness": s["name"], "level": s["level"], "seen_in_7_days": s["seen"],
            "usual_in_7_days": s["usual"], "expected_next_7_days": s["next7"]["mean"],
            "range_next_7_days": [s["next7"]["lo"], s["next7"]["hi"]], "mostly_aged": s["age"],
            "diagnosed_by_doctor": s["diagnosed"], "daily_counts_last_14_days": s["days"][-14:]}


@app.post("/api/predict/why", dependencies=[Depends(nurse)])
async def predict_why(q: Ask):
    try:
        return await ai.why(_evidence(q))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"CAIMEx did not answer ({type(e).__name__}). Try again.")


@app.post("/api/predict/draft", dependencies=[Depends(nurse)])
async def predict_draft(q: Ask):
    try:
        return await ai.draft(_evidence(q))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"CAIMEx did not answer ({type(e).__name__}). Try again.")


@app.get("/api/predict/briefing.mp3", dependencies=[Depends(nurse)])
async def briefing_audio():
    return await _mp3(voice.briefing_text(_prediction(), national.for_clinic()), "en")


@app.get("/api/say/warning.mp3", dependencies=[Depends(nurse)])
async def say_warning(disease: str, lang: str = "sn"):
    if disease not in national.DISEASES or lang not in config.LANGS:
        raise HTTPException(404)
    return await _mp3(voice.warn_text(lang, disease), lang)


def _rising() -> list[dict]:
    """What is rising, for the doctor and the pharmacy: the forecaster's numbers, never a model's."""
    return [{"area": s["area"], "illness": s["name"], "level": s["level"],
             "why": f"{s['seen']} in seven days, {s['usual']} is usual",
             "expected_next_week": s["next7"]["mean"], "range_next_week": [s["next7"]["lo"], s["next7"]["hi"]]}
            for s in prediction.predict()["signals"] if s["level"] in ("confirmed", "likely")]


@app.post("/api/visits/{sid}/consider", dependencies=[Depends(nurse)])
async def consider(sid: str):
    """The chat model's list of what the doctor may want to rule out. The doctor decides."""
    s = _visit(sid)
    if not s.get("note"):
        raise HTTPException(400, "The note is not written yet")
    area = ((s.get("details") or {}).get("area") or {}).get("value")
    local = "; ".join(f"{r['illness']} is {r['level']} in {r['area']}" for r in _rising() if r["area"] == area)
    try:
        out = await ai.consider(s, local)
    except Exception as e:
        raise HTTPException(502, f"CAIMEx did not answer ({type(e).__name__}). Try again.")
    visits.save()
    return out


# ── The doctor ─────────────────────────────────────────────────────────────

def _doctor_row(s: dict) -> dict:
    n = s.get("note") or {}
    signs = [x["label"] for x in s.get("live_signs", [])]
    return {**visits.vitals_row(s), "updated": s.get("updated") or s["created"],
            "stage": pharmacy.stage(s), "consult": s.get("consult"), "alarm": s.get("alarm"),
            "consider": s.get("consider"), "has_note": bool(s.get("note")),
            "patient": n.get("patient"), "complaint": n.get("chief_complaint"), "history": n.get("history") or [],
            "signs": signs + [f for f in n.get("red_flags") or [] if f not in signs and "?" not in f],
            "check": n.get("check_next") or [],
            "given": [{"med": r["med"], "qty": -r["qty"]} for r in pharmacy.given(s["id"])]}


@app.get("/api/doctor", dependencies=[Depends(nurse)])
async def doctor_state():
    order = {"emergency": 0, "urgent": 1, "routine": 2}
    rows = [_doctor_row(s) for s in visits.SESSIONS.values() if s["status"] in ("ready", "seen")]
    rows.sort(key=lambda r: (order.get(r["level"], 2), r["created"]))
    return {"visits": rows, "medicines": [{"id": m["id"], "name": m["name"], "unit": m["unit"], "stock": m["stock"]}
                                           for m in pharmacy.STATE["medicines"]],
            "diagnoses": pharmacy.DIAGNOSES, "how": pharmacy.HOW, "now": time.time()}


@app.post("/api/visits/{sid}/consult", dependencies=[Depends(nurse)])
async def set_consult(sid: str, body: Consult):
    """The doctor's diagnosis, outcome and prescription. Typed by the doctor: no model proposes them."""
    s = _visit(sid)
    if s["status"] not in ("ready", "seen"):
        raise HTTPException(400, "This patient is still speaking to the helper")
    try:
        pharmacy.consult(s, body.diagnosis, body.outcome, body.rx, body.suggested)
    except pharmacy.Refused as e:
        raise HTTPException(400, str(e))
    s["status"] = "seen"
    s["updated"] = time.time()
    visits.save()
    if pharmacy.stage(s) == "pharmacy":
        voice.call(s, "pharmacy")
    return _doctor_row(s)


@app.post("/api/pharmacy/adjust", dependencies=[Depends(nurse)])
async def pharmacy_adjust(body: Count):
    try:
        return pharmacy.adjust(body.med, body.counted, body.pin, body.reason)
    except pharmacy.Refused as e:
        _refuse(e)


@app.post("/api/visits/{sid}/fee", dependencies=[Depends(nurse)])
async def set_fee(sid: str, body: Fee):
    s = _visit(sid)
    try:
        pharmacy.set_fee(s, body.status, body.pin, body.reason)
    except pharmacy.Refused as e:
        _refuse(e)
    s["updated"] = time.time()
    visits.save()
    return visits.vitals_row(s)


@app.post("/api/visits/{sid}/note", dependencies=[Depends(nurse)])
async def write_note_again(sid: str):
    """The nurse asks for a note that could not be written to be written again."""
    s = _visit(sid)
    if s["status"] != "ready" or s.get("note"):
        raise HTTPException(409, "Only a visit waiting for the nurse, without a note, can have it written again")
    if not any(t["role"] == "user" for t in s["turns"]):
        raise HTTPException(409, "The patient said nothing to write a note from")
    visits.retry_note(s)
    return {"ok": True, "status": s["status"]}


@app.get("/api/counts", dependencies=[Depends(nurse)])
async def counts():
    """How much work waits at each staff screen, for the menu bar and the welcome page. Numbers only,
    counted as each screen counts them."""
    ss = list(visits.SESSIONS.values())
    waiting = [s for s in ss if s["status"] in ("summarising", "ready")]

    def level(s):
        return (s.get("triage") or {}).get("level")

    def measured(s):
        d = s.get("details") or {}
        return all((d.get(k) or {}).get("value") is not None for k in ("weight", "height", "bp"))

    return {"nurse": len(waiting),
            "emergency": sum(1 for s in waiting if level(s) == "emergency"),
            "vitals": sum(1 for s in waiting if level(s) != "emergency" and not measured(s)),
            "doctor": sum(1 for s in ss if s["status"] in ("ready", "seen") and pharmacy.stage(s) == "doctor"),
            "pharmacy": sum(1 for s in ss if s["status"] != "talking" and pharmacy.stage(s) == "pharmacy"),
            "order": sum(1 for m in pharmacy.forecast() if m["status"] in ("now", "none"))}


@app.get("/api/vitals", dependencies=[Depends(nurse)])
async def vitals():
    """The tickets waiting for the nurse, for the person at the scale. No complaint, no transcript."""
    rows = [visits.vitals_row(s) for s in visits.SESSIONS.values() if s["status"] in ("summarising", "ready")]
    return {"visits": sorted(rows, key=lambda r: r["number"]), "now": time.time()}


@app.get("/api/visits/{sid}/audio/{name}", dependencies=[Depends(nurse)])
async def patient_audio(sid: str, name: str):
    _visit(sid)
    if not re.fullmatch(r"\d{2}\.(webm|mp4|ogg|wav|mp3)", name):
        raise HTTPException(404)
    path = config.AUDIO_DIR / sid / name
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path)


@app.delete("/api/visits/{sid}", dependencies=[Depends(nurse)])
async def delete_visit(sid: str):
    """Remove one visit and its recordings."""
    _visit(sid)
    visits.remove(sid)
    return {"ok": True}


@app.delete("/api/visits", dependencies=[Depends(nurse)])
async def clear_all():
    """Empty the queue and delete every recording."""
    visits.clear()
    return {"ok": True}


# ── Voice check: the recogniser against what a real speaker typed ──────────

@app.post("/api/voicecheck", dependencies=[Depends(nurse)])
async def voice_check(audio: UploadFile = File(...), reference: str = Form(...),
                      speaker: str = Form(""), lang: str = Form("sn")):
    """The speaker types a sentence, then says it. The reference is theirs, so
    the error rate is measured against words no model wrote."""
    lang = lang if lang in config.LANGS else "sn"
    blob = await audio.read()
    mime = audio.content_type or "audio/webm"
    try:
        heard, call = await gateway.transcribe(blob, "check.wav", mime.split(";")[0], lang)
    except GatewayError as e:
        raise HTTPException(502, str(e)[:200])
    row = {"at": time.time(), "speaker": speaker.strip()[:40] or "unnamed", "lang": lang,
           "reference": reference.strip(), "heard": heard,
           "cer": metrics.cer(reference, heard), "wer": metrics.wer(reference, heard), "ms": call["ms"]}
    config.DATA.mkdir(parents=True, exist_ok=True)
    with config.VOICE_CHECK.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def _voice_rows() -> list[dict]:
    if not config.VOICE_CHECK.exists():
        return []
    rows = []
    for line in config.VOICE_CHECK.read_text().splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            pass
    return rows


def _voice_summary() -> dict:
    rows = [r for r in _voice_rows() if r.get("cer") is not None]
    speakers: dict[str, list[dict]] = {}
    for r in rows:
        speakers.setdefault(r["speaker"], []).append(r)
    return {
        "lines": len(rows),
        "speakers": [{"speaker": k, "lines": len(v),
                      "cer": round(statistics.mean(x["cer"] for x in v), 4),
                      "wer": round(statistics.mean(x["wer"] for x in v), 4)}
                     for k, v in sorted(speakers.items())],
        "cer": round(statistics.mean(r["cer"] for r in rows), 4) if rows else None,
    }


@app.get("/api/voicecheck", dependencies=[Depends(nurse)])
async def voice_check_summary():
    return {**_voice_summary(), "recent": _voice_rows()[-8:][::-1]}


# ── The Engine page: how CAIMEx is used, with live numbers ─────────────────

ROLES = [
    ("hear", "Hears the patient", "Speech to text", "/v1/audio/transcriptions", "STT_MODEL"),
    ("ask", "Chooses the next question", "Chat", "/v1/chat/completions", "CHAT_MODEL"),
    ("speak", "Speaks to the patient", "Text to speech", "/v1/audio/speech", "TTS_MODEL"),
    ("note", "Writes the nurse's note", "Chat, with reasoning", "/v1/chat/completions", "NOTE_MODEL"),
    ("second_opinion", "Gives a second opinion", "Decisions", "/v1/decisions", "DECISION_MODEL"),
    ("dictate", "Writes down the doctor's dictation", "Speech to text", "/v1/audio/transcriptions", "STT_MODEL"),
    ("syndrome", "Sorts each visit into a symptom group", "Chat", "/v1/chat/completions", "CHAT_MODEL"),
    ("brief", "Puts the forecast into a morning briefing", "Chat", "/v1/chat/completions", "NOTE_MODEL"),
    ("why", "Explains one warning from its numbers", "Chat", "/v1/chat/completions", "NOTE_MODEL"),
    ("draft", "Drafts the alert for a person to send", "Chat", "/v1/chat/completions", "NOTE_MODEL"),
    ("consider", "Lists what the doctor may rule out", "Chat, with reasoning", "/v1/chat/completions", "NOTE_MODEL"),
    ("reorder", "Advises what the pharmacy should order", "Chat", "/v1/chat/completions", "NOTE_MODEL"),
]


@app.get("/api/engine")
async def engine():
    calls = [c for s in visits.SESSIONS.values() for c in s["trace"] if c.get("step") != "consider"] + ai.CALLS
    steps = []
    for step, does, service, path, attr in ROLES:
        model = getattr(config, attr)
        mine = [c for c in calls if c["step"] == step and not c.get("cached")]
        info = CATALOGUE.get(model, {})
        steps.append({
            "step": step, "does": does, "service": service, "path": path, "model": model,
            "hosting": info.get("hosting_kind"), "country": info.get("hosting_country"),
            "calls": len(mine),
            "median_ms": round(statistics.median(c["ms"] for c in mine)) if mine else None,
            "cost": round(sum(c.get("cost") or 0 for c in mine), 6),
        })
    done = [s for s in visits.SESSIONS.values() if s["status"] in ("ready", "seen")]
    # A visit's cost only means something when the patient really spoke:
    # typed and sample-filled visits skip the recogniser, which is most of the bill.
    spoken = [s for s in done if any(c["step"] == "hear" for c in s["trace"])]
    costs = [sum(c.get("cost") or 0 for c in s["trace"]) for s in spoken]
    heard = [sum(c.get("cost") or 0 for c in s["trace"] if c["step"] == "hear") for s in spoken]
    try:
        results = json.loads((config.EVAL / "results.json").read_text())
    except (OSError, ValueError):
        results = None
    issues = _issues()
    try:
        held = json.loads((config.EVAL / "heldout_results.json").read_text())
        held = {k: held.get(k) for k in ("ran_at", "rules_alone", "pipeline", "rules_alone_after_fixes")}
    except (OSError, ValueError):
        held = None
    spoke = [c for c in calls if c["step"] == "speak"]
    last = max((s for s in done if s["trace"]), key=lambda s: s["updated"], default=None)
    return {
        "issue_rows": issues, "heldout": held,
        "saved_line_share": round(sum(1 for c in spoke if c.get("cached")) / len(spoke), 2) if spoke else None,
        "last_visit": {"number": last["number"], "sample": last["sample"], "trace": last["trace"],
                       "level": (last.get("triage") or {}).get("level"),
                       "cost": round(sum(c.get("cost") or 0 for c in last["trace"]), 5)} if last else None,
        "steps": steps, "voice": config.TTS_VOICE,
        "visits": len(done),
        "cost_per_visit": round(statistics.mean(costs), 4) if costs else None,
        "cost_share_hearing": round(sum(heard) / sum(costs), 3) if costs and sum(costs) else None,
        "spoken_visits": len(spoken), "prices": gateway.PRICES,
        "cached_lines": sum(1 for c in calls if c["step"] == "speak" and c.get("cached")),
        "evaluation": results, "voicecheck": _voice_summary(), "issues": len(issues),
        "rules": [{"label": r.label, "level": r.level, "source": triage.SOURCES.get(r.source, r.source)}
                  for r in triage.RULES],
        "max_questions": prompts.MAX_QUESTIONS, "keep_hours": config.KEEP_HOURS,
    }


# ── Pages ──────────────────────────────────────────────────────────────────

@app.get("/nurse")
async def nurse_page():
    return FileResponse(config.WEB / "nurse.html")


@app.get("/outbreaks")
async def outbreaks_page():
    return FileResponse(config.WEB / "outbreaks.html")


@app.get("/national")
async def national_page():
    return FileResponse(config.WEB / "national.html")


@app.get("/board")
async def board_page():
    return FileResponse(config.WEB / "board.html")


@app.get("/doctor")
async def doctor_page():
    return FileResponse(config.WEB / "doctor.html")


@app.get("/pharmacy")
async def pharmacy_page():
    return FileResponse(config.WEB / "pharmacy.html")


@app.get("/vitals")
async def vitals_page():
    return FileResponse(config.WEB / "vitals.html")


@app.get("/engine")
async def engine_page():
    return FileResponse(config.WEB / "engine.html")


@app.get("/check")
async def check_page():
    return FileResponse(config.WEB / "check.html")


@app.get("/demo")
async def demo_page():
    return FileResponse(config.WEB / "demo.html")


@app.get("/welcome")
async def welcome_page():
    return FileResponse(config.WEB / "welcome.html")


app.mount("/", StaticFiles(directory=config.WEB, html=True), name="web")
