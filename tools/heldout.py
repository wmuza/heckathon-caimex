"""Check Mukoti on eval/heldout.json: statements it was not written against.

  uv run python tools/heldout.py              # the rules alone (no network)
  uv run python tools/heldout.py --pipeline   # the whole pipeline on each opening statement

Each item is one opening statement. With --pipeline the statement is given as
the patient's first line, the visit is ended there, and the note and second
opinion are written, so the result is what the nurse would see if the patient
said only that. Writes eval/heldout_results.json.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MUKOTI_DATA", tempfile.mkdtemp(prefix="mukoti-heldout-"))

from app import config, gateway, triage, visits  # noqa: E402


def tally(rows: list[dict], key: str) -> dict:
    by = {lvl: [r for r in rows if r["expect"] == lvl] for lvl in triage.LEVELS}
    return {
        "items": len(rows),
        "emergencies": len(by["emergency"]),
        "emergencies_given_emergency": sum(1 for r in by["emergency"] if r[key] == "emergency"),
        "emergencies_given_urgent": [r["id"] for r in by["emergency"] if r[key] == "urgent"],
        "emergencies_left_routine": [r["id"] for r in by["emergency"] if r[key] == "routine"],
        "urgent": len(by["urgent"]),
        "urgent_given_urgent_or_higher": sum(1 for r in by["urgent"] if r[key] != "routine"),
        "urgent_left_routine": [r["id"] for r in by["urgent"] if r[key] == "routine"],
        "routine": len(by["routine"]),
        "routine_kept_routine": sum(1 for r in by["routine"] if r[key] == "routine"),
        "routine_raised": [r["id"] for r in by["routine"] if r[key] != "routine"],
    }


async def pipeline(item: dict, sem: asyncio.Semaphore) -> dict:
    async with sem:
        s = visits.new(item["lang"])
        try:
            async for _ in visits.take_turn(s, text=item["text"], want_audio=False):
                pass
            if s["status"] == "talking":
                visits.finish(s)
            # Wait for the note here, inside the limit: sixty notes asked for at
            # once got a 504 from the gateway on every one of them.
            await visits.wait_for_notes()
        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}"[:160]}
    return {"s": s}


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pipeline", action="store_true")
    a = ap.parse_args()
    data = json.loads((config.EVAL / "heldout.json").read_text())
    rows = []
    for it in data["items"]:
        hits = triage.scan(it["text"], it["lang"])
        rows.append({"id": it["id"], "lang": it["lang"], "expect": it["expect"], "sign": it["sign"],
                     "text": it["text"], "rules": triage.highest([r.level for r in hits]),
                     "rule_signs": [r.label for r in hits]})
    out = {"ran_at": time.strftime("%Y-%m-%d %H:%M"), "about": data["about"], "rules_alone": tally(rows, "rules")}
    if a.pipeline:
        gateway.start()
        await gateway.load_prices()
        sem = asyncio.Semaphore(2)
        got = await asyncio.gather(*(pipeline(it, sem) for it in data["items"]))
        await visits.wait_for_notes()
        await gateway.stop()
        for r, g in zip(rows, got):
            s = g.get("s")
            r["pipeline"] = (s["triage"] or {}).get("level") if s else "routine"   # a failure counts as a miss
            r["alarm_during_talk"] = bool(s and s["alarm"])
            r["checks"] = {c["name"]: c["level"] for c in (s["triage"] or {}).get("checks", [])} if s else {}
            r["error"] = g.get("error") or (s and s["error"])
        out["pipeline"] = tally(rows, "pipeline")
        out["pipeline"]["emergencies_alarmed_on_the_sentence"] = sum(
            1 for r in rows if r["expect"] == "emergency" and r["alarm_during_talk"])
    out["rows"] = rows
    path = config.EVAL / "heldout_results.json"
    try:
        old = json.loads(path.read_text())
    except (OSError, ValueError):
        old = {}
    if not a.pipeline and "pipeline" in old:      # keep the last pipeline run beside a rules-only run
        out["pipeline"] = old["pipeline"]
        for r, o in zip(rows, old.get("rows", [])):
            for k in ("pipeline", "alarm_during_talk", "checks"):
                if k in o:
                    r[k] = o[k]
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps({k: out[k] for k in ("rules_alone", "pipeline") if k in out}, indent=1))
    for r in rows:
        got = r.get("pipeline", r["rules"])
        bad = triage.rank(got) < triage.rank(r["expect"])
        over = triage.rank(got) > triage.rank(r["expect"])
        if bad or over:
            print(("LOW  " if bad else "high ") + f"{r['id']} {r['lang']} expect={r['expect']:<9} rules={r['rules']:<9} "
                  f"pipeline={r.get('pipeline', '-'):<9} | {r['sign'][:40]} | {r['text'][:90]}")


if __name__ == "__main__":
    asyncio.run(main())
