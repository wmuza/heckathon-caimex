"""Stock, dispensing and the approvals a supervisor must sign.

Three controls, none of which uses a model:

1. A medicine is dispensed against a ticket, once per ticket. The page shows
   the ticket's photo beside the photos of everyone else who was given the
   same medicine today, so a person can see one face collecting twice.
   Nothing here compares faces by itself.
2. A fee waiver, a second supply on one ticket and a change to a stock count
   are refused without the supervisor's PIN and a reason. Each is logged.
3. The days of stock left are worked out from what was dispensed in the last
   fortnight, and a medicine is flagged four weeks before it would run out.

Mukoti does not diagnose, so use is counted by medicine dispensed, not by
diagnosis. The stock history a new installation starts with is made up, and
every such row is marked "demo".
"""

from __future__ import annotations

import json
import random
import time

from . import config

DAY = 86400
RATE_DAYS = 14          # use is averaged over this many days
ORDER_SOON_DAYS = 28    # flagged this long before the shelf would be empty
ORDER_NOW_DAYS = 14
MAX_AT_ONCE = 200       # the most units one dispensing may take: above it is a typing slip

# id, name, unit, stock on hand, made-up use a day (low, high)
SEED = [
    ("insulin", "Insulin, 10 ml vial", "vials", 34, (2, 6)),
    ("amlodipine", "Amlodipine 5 mg", "tablets", 1500, (40, 100)),
    ("hctz", "Hydrochlorothiazide 25 mg", "tablets", 4200, (30, 90)),
    ("metformin", "Metformin 500 mg", "tablets", 6800, (60, 150)),
    ("amoxicillin", "Amoxicillin 500 mg", "capsules", 2100, (60, 130)),
    ("paracetamol", "Paracetamol 500 mg", "tablets", 9000, (80, 200)),
    ("ors", "Oral rehydration salts", "sachets", 420, (4, 14)),
]
WAIVER_REASONS = ("Child under five", "Pregnant", "Aged 65 or over", "Cannot pay, assessed", "Other")

STATE: dict = {}


class Refused(ValueError):
    """Not done. The message is shown to the member of staff."""


class NeedsSupervisor(Refused):
    """Not done without the supervisor's PIN and a reason."""


def _path():
    return config.DATA / "pharmacy.json"


def _seed(now: float) -> dict:
    rng = random.Random(2026)
    log = []
    for mid, _, _, _, (low, high) in SEED:
        for back in range(RATE_DAYS * 2, 0, -1):
            log.append({"at": now - back * DAY, "kind": "dispense", "med": mid, "qty": -rng.randint(low, high),
                        "demo": True})
    return {"medicines": [{"id": m, "name": n, "unit": u, "stock": s} for m, n, u, s, _ in SEED],
            "log": sorted(log, key=lambda r: r["at"])}


def load(now: float | None = None) -> None:
    STATE.clear()
    try:
        STATE.update(json.loads(_path().read_text()))
    except (OSError, ValueError):
        STATE.update(_seed(now or time.time()))
        save()


def save() -> None:
    config.DATA.mkdir(parents=True, exist_ok=True)
    tmp = _path().with_suffix(".tmp")
    tmp.write_text(json.dumps(STATE, ensure_ascii=False))
    tmp.replace(_path())


def _med(mid: str) -> dict:
    if not STATE:
        load()
    for m in STATE["medicines"]:
        if m["id"] == mid:
            return m
    raise Refused("Unknown medicine")


def supervisor(pin: str | None) -> bool:
    import hmac
    return bool(pin) and hmac.compare_digest(str(pin).encode(), config.SUPERVISOR_PIN.encode())


def _approve(pin: str | None, reason: str | None, what: str) -> str:
    reason = (reason or "").strip()[:120]
    if not supervisor(pin):
        raise NeedsSupervisor(f"{what} needs the supervisor's PIN")
    if not reason:
        raise NeedsSupervisor(f"{what} needs a reason")
    return reason


def forecast(now: float | None = None) -> list[dict]:
    """Each medicine with its use a day over the last fortnight and the days of stock left."""
    if not STATE:
        load()
    now = now or time.time()
    used: dict[str, int] = {}
    for r in STATE["log"]:
        if r["kind"] == "dispense" and r["at"] > now - RATE_DAYS * DAY:
            used[r["med"]] = used.get(r["med"], 0) - r["qty"]
    why: dict[str, dict[str, int]] = {}
    for r in STATE["log"]:
        if r["kind"] == "dispense" and r.get("dx") and r["at"] > now - RATE_DAYS * DAY:
            why.setdefault(r["med"], {})[r["dx"]] = why.get(r["med"], {}).get(r["dx"], 0) - r["qty"]
    out = []
    for m in STATE["medicines"]:
        m = {**m, "for": [d for d, _ in sorted(why.get(m["id"], {}).items(), key=lambda kv: -kv[1])[:2]]}
        per_day = used.get(m["id"], 0) / RATE_DAYS
        days = m["stock"] / per_day if per_day > 0 else None
        status = "none" if m["stock"] <= 0 else "enough" if days is None or days >= ORDER_SOON_DAYS \
            else "now" if days < ORDER_NOW_DAYS else "soon"
        out.append({**m, "per_day": round(per_day, 1), "days_left": None if days is None else int(days),
                    "status": status})
    return sorted(out, key=lambda m: (m["days_left"] is None, m["days_left"] or 0))


DIAGNOSES = ("High blood pressure", "Diabetes", "Chest infection", "Malaria", "Diarrhoea", "Injury",
             "Pregnancy care", "Headache")       # quick picks for the doctor, who may type any other
OUTCOMES = ("treated", "referred", "admitted", "come_in")
ONLINE_OUTCOMES = ("treated", "come_in")    # at home: treated with an e-prescription, or come to the hospital
HOW = ("Once a day", "Twice a day", "Three times a day", "When needed", "As directed")    # keys of prompts.HOW_SAY


def consult(visit: dict, diagnosis: str, outcome: str, rx: list, suggested: bool = False) -> dict:
    """The doctor's part of the visit: a diagnosis the doctor typed, the outcome and the prescription.
    No model proposes any of it."""
    diagnosis = " ".join((diagnosis or "").split())[:120]
    if not diagnosis:
        raise Refused("Type the diagnosis")
    if outcome not in OUTCOMES:
        raise Refused("Choose what happens next")
    if visit.get("online") and outcome not in ONLINE_OUTCOMES:
        raise Refused("For a patient at home, choose treat at home or come to the hospital")
    if outcome == "come_in" and not visit.get("online"):
        raise Refused("Come to the hospital is only for a patient at home")
    lines, seen = [], set()
    for line in rx or []:
        m = _med(str(line.get("med")))
        try:
            qty = int(line.get("qty"))
        except (TypeError, ValueError):
            raise Refused(f"Type how many {m['unit']} of {m['name']}")
        if not 1 <= qty <= MAX_AT_ONCE:
            raise Refused(f"One supply is between 1 and {MAX_AT_ONCE} {m['unit']}")
        if m["id"] in seen:
            raise Refused(f"{m['name']} is on the prescription twice")
        seen.add(m["id"])
        lines.append({"med": m["id"], "qty": qty, "how": str(line.get("how") or "As directed")[:60]})
    visit["consult"] = {"diagnosis": diagnosis, "outcome": outcome, "rx": lines, "at": time.time(),
                        "suggested": bool(suggested)}       # true when the doctor took the wording from the model's list
    return visit["consult"]


def remaining(visit: dict, mid: str) -> int:
    """How many units of a medicine the prescription still allows this ticket."""
    want = sum(l["qty"] for l in (visit.get("consult") or {}).get("rx", []) if l["med"] == mid)
    return max(0, want + sum(r["qty"] for r in given(visit["id"]) if r["med"] == mid))


def stage(visit: dict) -> str:
    """Where the patient is: intake, nurse, doctor, pharmacy or done."""
    if visit["status"] == "talking":
        return "intake"
    if visit.get("consult"):
        if visit.get("online"):
            return "done"          # an e-prescription: bought at any pharmacy, never dispensed here
        owed = any(remaining(visit, l["med"]) for l in visit["consult"]["rx"])
        return "pharmacy" if owed else "done"
    return "doctor" if visit["status"] == "seen" else "nurse"


def given(sid: str, since: float = 0) -> list[dict]:
    return [r for r in STATE.get("log", []) if r["kind"] == "dispense" and r.get("sid") == sid and r["at"] >= since]


def dispense(sid: str, number: int, mid: str, qty, pin: str | None = None, reason: str | None = None,
             allowed: int = 0, diagnosis: str | None = None) -> dict:
    """Give a medicine against a ticket. `allowed` is what the doctor's prescription still allows.
    Anything beyond it (not prescribed, more than prescribed, a second supply) needs the supervisor."""
    m = _med(mid)
    try:
        qty = int(qty)
    except (TypeError, ValueError):
        raise Refused("Type how many as a whole number")
    if not 1 <= qty <= MAX_AT_ONCE:
        raise Refused(f"One supply is between 1 and {MAX_AT_ONCE} {m['unit']}")
    if qty > m["stock"]:
        raise Refused(f"Only {m['stock']} {m['unit']} on the shelf")
    row = {"at": time.time(), "kind": "dispense", "med": mid, "qty": -qty, "sid": sid, "ticket": number}
    if diagnosis:
        row["dx"] = diagnosis
    if qty > allowed:
        had = any(r["med"] == mid for r in given(sid))
        why = f"Ticket {number} has already received its {m['name']}. A second supply" if had and not allowed \
            else f"The prescription for ticket {number} allows {allowed} {m['unit']} of {m['name']}. More than that" if allowed \
            else f"{m['name']} is not on the prescription for ticket {number}. Dispensing it"
        row["reason"] = _approve(pin, reason, why)
        row["approved"] = "supervisor"
    m["stock"] -= qty
    STATE["log"].append(row)
    save()
    return row


def adjust(mid: str, counted, pin: str | None, reason: str | None) -> dict:
    """Set the shelf count after a stock take or a delivery. Always the supervisor's."""
    m = _med(mid)
    try:
        counted = int(counted)
    except (TypeError, ValueError):
        raise Refused("Type the count as a whole number")
    if not 0 <= counted <= 1_000_000:
        raise Refused("That count is not believable")
    reason = _approve(pin, reason, "A change to a stock count")
    row = {"at": time.time(), "kind": "adjust", "med": mid, "qty": counted - m["stock"], "was": m["stock"],
           "now": counted, "reason": reason, "approved": "supervisor"}
    m["stock"] = counted
    STATE["log"].append(row)
    save()
    return row


def set_fee(visit: dict, status: str, pin: str | None = None, reason: str | None = None) -> dict:
    """Mark a visit's fee as due, paid or waived. A waiver needs the supervisor."""
    if status not in ("due", "paid", "waived"):
        raise Refused("Unknown fee status")
    fee = {"status": status, "at": time.time()}
    if status == "waived":
        fee["reason"] = _approve(pin, reason, "A fee waiver")
        fee["approved"] = "supervisor"
        if not STATE:
            load()
        STATE["log"].append({"at": fee["at"], "kind": "waiver", "sid": visit["id"], "ticket": visit["number"],
                             "reason": fee["reason"], "approved": "supervisor"})
        save()
    visit["fee"] = fee
    return fee


def approvals(since: float) -> list[dict]:
    """Everything the supervisor signed since a time, newest first."""
    names = {m["id"]: m["name"] for m in STATE.get("medicines", [])}
    out = [{**r, "name": names.get(r.get("med"))} for r in STATE.get("log", [])
           if r.get("approved") and r["at"] >= since]
    return sorted(out, key=lambda r: -r["at"])
