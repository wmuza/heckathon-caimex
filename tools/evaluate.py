"""Run every made-up patient through the real pipeline and write eval/results.json.

  uv run python tools/evaluate.py            # typed lines (fast)
  uv run python tools/evaluate.py --spoken   # each line synthesised, then recognised
  uv run python tools/evaluate.py --only baby-breathing,bp-refill

What this measures: whether Mukoti, end to end, gives each made-up patient at
least the level it was written to deserve, and what a visit costs and takes.

What it does NOT measure: clinical accuracy (the patients and their expected
levels were written by an AI assistant, not a clinician) or the recogniser on
real voices (the spoken run uses synthetic speech, which is easier than a
person in a waiting room). Use the /check page for real voices.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MUKOTI_DATA", tempfile.mkdtemp(prefix="mukoti-eval-"))

from app import config, gateway, metrics, samples, triage, visits  # noqa: E402


async def one(p: dict, spoken: bool, sem: asyncio.Semaphore) -> dict:
    async with sem:
        t0 = time.time()
        try:
            s = await samples.run(p, spoken=spoken)
            await visits.wait_for_notes()      # inside the limit, so notes are never asked for all at once
            error = None
        except Exception as e:
            return {"id": p["id"], "lang": p["lang"], "expect": p["expect"], "level": None,
                    "error": f"{type(e).__name__}: {e}"[:200]}
        talk = time.time() - t0
    return {"s": s, "p": p, "talk": talk, "error": error}


def row(r: dict, spoken: bool) -> dict:
    if "s" not in r:
        return r
    s, p = r["s"], r["p"]
    t = s["triage"] or {}
    level = t.get("level")
    patient_turns = [x for x in s["turns"] if x["role"] == "user"]
    out = {
        "id": p["id"], "title": p["title"], "lang": p["lang"], "expect": p["expect"], "level": level,
        "under": triage.rank(level) < triage.rank(p["expect"]),
        "over": triage.rank(level) > triage.rank(p["expect"]),
        "checks": {c["name"]: c["level"] for c in t.get("checks", [])},
        "raised_by": t.get("raised_by"), "alarm": s["alarm"], "alarm_by": s["alarm_by"],
        "alarm_on_turn": len(patient_turns) if s["alarm"] else None,
        "patient_turns": len(patient_turns),
        "cost": round(sum(c.get("cost") or 0 for c in s["trace"]), 6),
        "cost_hearing": round(sum(c.get("cost") or 0 for c in s["trace"] if c["step"] == "hear"), 6),
        "audio_seconds": round(sum(c.get("seconds") or 0 for c in s["trace"] if c["step"] == "hear"), 1),
        "note_ok": s["note"] is not None, "error": s["error"],
        "questions": [x["text"] for x in s["turns"] if x["role"] == "assistant"][1:],
        "ms": {step: [c["ms"] for c in s["trace"] if c["step"] == step and not c.get("cached")]
               for step in ("hear", "ask", "speak", "note", "second_opinion")},
    }
    if spoken:
        # How faithfully the synthetic line came back through the recogniser.
        said = [samples.line(p, "main")]
        topics = [x.get("topic") for x in s["turns"] if x["role"] == "assistant"][1:]
        said += [samples.line(p, tp) for tp in topics if tp][:len(patient_turns) - 1]
        pairs = list(zip(said, [x["text"] for x in patient_turns]))
        cers = [c for c in (metrics.cer(a, b) for a, b in pairs) if c is not None]
        # A line the recogniser returned empty never became a turn. Count it as wholly wrong.
        unheard = max(0, sum(1 for c in s["trace"] if c["step"] == "hear") - len(patient_turns))
        out["lines_not_heard"] = unheard
        cers += [1.0] * unheard
        out["round_trip_cer"] = round(statistics.mean(cers), 4) if cers else None
    return out


def summary(rows: list[dict]) -> dict:
    ok = [r for r in rows if r.get("level")]
    by = {lvl: [r for r in ok if r["expect"] == lvl] for lvl in triage.LEVELS}
    ms = {step: [m for r in ok for m in r["ms"][step]] for step in ("hear", "ask", "speak", "note", "second_opinion")}
    emerg = [r for r in rows if r["expect"] == "emergency"]
    out = {
        "patients": len(rows), "completed": len(ok), "failed": len(rows) - len(ok),
        "expected": {lvl: len(v) for lvl, v in by.items()},
        "exact": sum(1 for r in ok if r["level"] == r["expect"]),
        # A visit that failed counts against us unless the patient was routine anyway.
        "under_triaged": [r["id"] for r in ok if r["under"]]
        + [r["id"] for r in rows if not r.get("level") and r["expect"] != "routine"],
        "over_triaged": [r["id"] for r in ok if r["over"]],
        "emergencies": len(emerg),
        "emergencies_caught": sum(1 for r in emerg if r["level"] == "emergency"),
        "emergencies_alarmed_during_talk": sum(1 for r in emerg if r["alarm"]),
        "emergencies_alarmed_first_sentence": sum(1 for r in emerg if r["alarm_on_turn"] == 1),
        "routine_kept_routine": sum(1 for r in by["routine"] if r["level"] == "routine"),
        "notes_written": sum(1 for r in ok if r["note_ok"]),
        "median_ms": {k: round(statistics.median(v)) if v else None for k, v in ms.items()},
        "cost_per_visit": round(statistics.mean(r["cost"] for r in ok), 5) if ok else None,
        "cost_hearing_share": round(sum(r["cost_hearing"] for r in ok) / max(1e-9, sum(r["cost"] for r in ok)), 3),
        "audio_seconds_per_visit": round(statistics.mean(r["audio_seconds"] for r in ok), 1) if ok else None,
        "cost_total": round(sum(r["cost"] for r in ok), 4),
    }
    cers = [r["round_trip_cer"] for r in ok if r.get("round_trip_cer") is not None]
    if cers:
        out["round_trip_cer"] = round(statistics.mean(cers), 4)
    return out


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spoken", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--parallel", type=int, default=3)
    ap.add_argument("--out", default=str(config.EVAL / "results.json"))
    a = ap.parse_args()

    gateway.start()
    await gateway.load_prices()
    await asyncio.gather(*(gateway.client.get("/models", params={"kind": "stt"}) for _ in range(a.parallel)))
    todo = samples.all_patients()
    if a.only:
        todo = [p for p in todo if p["id"] in a.only.split(",")]
    sem = asyncio.Semaphore(a.parallel)
    t0 = time.time()
    raw = await asyncio.gather(*(one(p, a.spoken, sem) for p in todo))
    await visits.wait_for_notes()
    rows = [row(r, a.spoken) for r in raw]
    await gateway.stop()

    mode = "spoken" if a.spoken else "typed"
    result = {
        "ran_at": time.strftime("%Y-%m-%d %H:%M"), "mode": mode, "seconds": round(time.time() - t0),
        "models": {"hear": config.STT_MODEL, "ask": config.CHAT_MODEL, "speak": config.TTS_MODEL,
                   "note": config.NOTE_MODEL, "second_opinion": config.DECISION_MODEL},
        "caveat": ("Made-up patients written by an AI assistant. Expected levels set from the published "
                   "tools in docs/SOURCES.md by the same assistant, not by a clinician. The rules and "
                   "these patients were written together, so this shows the pipeline holds together, "
                   "not how it does on patients it has never seen. "
                   + ("Spoken lines are synthetic speech, which is easier to recognise than a real patient. "
                      "Speech costs are worked out from the catalogue's price list, because the gateway "
                      "reports none." if a.spoken else
                      "Lines were typed, so this run leaves out the recogniser and its cost.")),
        "summary": summary(rows), "rows": rows,
    }
    out = Path(a.out)
    if not a.only:
        try:
            existing = json.loads(out.read_text())
        except (OSError, ValueError):
            existing = {}
        existing[mode] = result
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(existing, ensure_ascii=False, indent=1))
    sm = result["summary"]
    print(json.dumps(sm, indent=1))
    for r in rows:
        flag = "UNDER" if r.get("under") else "over " if r.get("over") else "ok   "
        print(f"{flag} {r['id']:<22} expect={r['expect']:<9} got={str(r.get('level')):<9} "
              f"turns={r.get('patient_turns')} alarm={r.get('alarm')} checks={r.get('checks')} err={r.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
