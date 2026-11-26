"""Outbreak watch: is one kind of illness rising in one area, and in whom?

No model is used and nothing here is a forecast from a trained model. The rule
is the plain one disease-surveillance officers use, so anyone can check it:

  A SIGNAL is raised for a symptom group in an area when this week's count is
  at least 5 and is above what is usual there (the mean of the four weeks
  before, plus twice the square root of that mean).

Each area then gets one of four levels:
  confirmed  a signal, and a doctor diagnosed at least 3 of this week's cases
  likely     a signal, not yet confirmed by a doctor's diagnoses
  watch      no signal there, but it borders an area that is confirmed
  usual      nothing above the usual

"Confirmed" means diagnosed by the clinic's doctor. It does not mean a
laboratory result. The projection for next week assumes the rise continues at
the rate of the last two weeks, which real outbreaks do not promise.

What is kept is a tally with no name and no ticket: the day, the area, the age
band, the symptom group and whether a doctor diagnosed it. It outlives the
visit (which is deleted after a day) so that weeks can be compared.

The areas, their map and the history a new installation starts with are made up.
"""

from __future__ import annotations

import json
import math
import random
import re
import time

from . import config

DAY = 86400
HISTORY_DAYS = 91           # how far back the tally is kept: twelve weeks to learn the usual from, and one to judge
WEEKS = 5                   # this week and the four before it
MIN_CASES = 5
CONFIRM_AT = 3
AGE_SHARE = 0.6             # an age band is named when it holds this share of the week's cases

# The catchment, as a 3 by 3 grid of made-up wards. The clinic is in the middle one.
AREAS = [f"Ward {n}" for n in range(1, 10)]
CLINIC = "Ward 5"


def neighbours(area: str) -> list[str]:
    i = AREAS.index(area)
    r, c = divmod(i, 3)
    return [AREAS[rr * 3 + cc] for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            if 0 <= rr < 3 and 0 <= cc < 3]


BANDS = [(0, 4, "under 5"), (5, 12, "5 to 12"), (13, 27, "13 to 27"), (28, 49, "28 to 49"), (50, 200, "50 and over")]

# Symptom groups, read from the note's complaint and what the patient said. The first that matches wins.
SYNDROMES = [
    ("diarrhoea", "Diarrhoea or vomiting", "vomiting", r"diarrh|manyoka|vomit|rutsa|runny stomach|loose stool|cholera|typhoid|gastro|dysentery"),
    ("fever_neck", "Fever with a stiff neck", "neck", r"stiff neck|mutsipa"),
    ("breathing", "Cough or trouble breathing", "breathing", r"cough|kosora|breath|kufema|chest infection|wheez|flu\b"),
    ("fever", "Fever", "fever", r"fever|kupisa|\bhot\b|malaria|fivha"),
]
NAME = {k: n for k, n, _, _ in SYNDROMES}
PICTURE = {k: p for k, _, p, _ in SYNDROMES}

STATE: dict = {}


def _path():
    return config.DATA / "surveillance.json"


def band(age: dict | None) -> str | None:
    if not age or age.get("value") is None:
        return None
    years = age["value"] if age.get("unit") == "years" else 0
    return next(name for low, high, name in BANDS if low <= years <= high)


def syndrome(text: str) -> str | None:
    text = (text or "").lower()
    return next((k for k, _, _, rx in SYNDROMES if re.search(rx, text)), None)


def _seed(now: float) -> list[dict]:
    """Made-up history: a low, steady background everywhere, and two planted rises."""
    rng = random.Random(11)
    bands = [b[2] for b in BANDS]
    rows = []

    def add(day, area, synd, age, confirmed=False):
        rows.append({"at": now - day * DAY - rng.randint(0, DAY - 1), "area": area, "syndrome": synd, "band": age,
                     "confirmed": confirmed, "demo": True})

    # Twelve weeks of background, busier on Mondays and quiet at the weekend, as clinics are.
    week = (1.35, 1.15, 1.05, 1.0, 0.95, 0.5, 0.3)
    for day in range(HISTORY_DAYS):
        w = week[(int((now + 7200) // DAY) - day + 3) % 7]
        for area in AREAS:
            for synd, rate in (("diarrhoea", 0.33), ("fever", 0.44), ("breathing", 0.5), ("fever_neck", 0.02)):
                for _ in range(2):
                    if rng.random() < rate * w / 2:
                        add(day, area, synd, rng.choice(bands))
    young = lambda: "13 to 27" if rng.random() < 0.75 else rng.choice(bands)
    small = lambda: "under 5" if rng.random() < 0.7 else rng.choice(bands)
    for day, n in ((13, 1), (11, 1), (9, 2), (8, 2), (6, 2), (5, 3), (4, 3), (3, 3), (2, 4), (1, 4), (0, 3)):
        for i in range(n):          # diarrhoea in Ward 3, mostly aged 13 to 27, with the doctor's diagnoses
            add(day, "Ward 3", "diarrhoea", young(), confirmed=day <= 4 and i == 0)
    for day, n in ((5, 1), (4, 2), (3, 2), (2, 2), (1, 3), (0, 2)):
        for _ in range(n):          # the same starting next door, not yet diagnosed
            add(day, "Ward 6", "diarrhoea", young())
    for day, n in ((6, 1), (5, 1), (4, 2), (3, 2), (2, 3), (1, 2), (0, 3)):
        for _ in range(n):          # fever in small children in Ward 7
            add(day, "Ward 7", "fever", small())
    return rows


def load(now: float | None = None) -> None:
    STATE.clear()
    try:
        STATE.update(json.loads(_path().read_text()))
    except (OSError, ValueError):
        STATE.update({"events": _seed(now or time.time())})
        save()


def save() -> None:
    config.DATA.mkdir(parents=True, exist_ok=True)
    tmp = _path().with_suffix(".tmp")
    tmp.write_text(json.dumps(STATE, ensure_ascii=False))
    tmp.replace(_path())


def sync(sessions: dict) -> None:
    """Carry each finished visit into the tally, updating its row while the visit lives.
    Only the area, the age band, the symptom group and whether a doctor diagnosed it are kept."""
    if not STATE:
        load()
    by_key = {e["key"]: e for e in STATE["events"] if e.get("key")}
    changed = False
    for s in sessions.values():
        if s.get("status") == "talking" or s.get("sample"):       # sample patients are not cases
            continue
        d = s.get("details") or {}
        area = (d.get("area") or {}).get("value")
        said = " ".join(t.get("en") or t["text"] for t in s["turns"] if t["role"] == "user")
        # The chat model's grouping when it gave one ("" means it said none); fixed words when it did not answer.
        synd = (s["syndrome"] or None) if "syndrome" in s else \
            syndrome(((s.get("note") or {}).get("chief_complaint") or "") + " " + said)
        if not area or not synd:
            continue
        # Confirmed only when the doctor's own diagnosis is of this kind of illness: a doctor who
        # diagnosed a sprain has not confirmed an outbreak of diarrhoea.
        dx = (s.get("consult") or {}).get("diagnosis") or ""
        row = {"key": s["id"], "at": s["created"], "area": area, "syndrome": synd, "band": band(d.get("age")),
               "confirmed": bool(dx) and syndrome(dx) == synd}
        if by_key.get(s["id"]) != row:
            if s["id"] in by_key:
                by_key[s["id"]].update(row)
            else:
                STATE["events"].append(row)
            changed = True
    cutoff = time.time() - (HISTORY_DAYS + 7) * DAY
    kept = [e for e in STATE["events"] if e["at"] >= cutoff]
    if changed or len(kept) != len(STATE["events"]):
        STATE["events"] = kept
        save()


def _threshold(usual: float) -> float:
    return usual + 2 * math.sqrt(usual)


def analyse(now: float | None = None) -> dict:
    if not STATE:
        load()
    now = now or time.time()
    weeks: dict[tuple[str, str], list[list[dict]]] = {}
    for e in STATE["events"]:
        w = int((now - e["at"]) // (7 * DAY))                    # 0 is the last seven days
        if 0 <= w < WEEKS:
            weeks.setdefault((e["area"], e["syndrome"]), [[] for _ in range(WEEKS)])[w].append(e)
    signals = []
    for (area, synd), ws in weeks.items():
        counts = [len(w) for w in ws]
        usual = sum(counts[1:]) / (WEEKS - 1)
        if counts[0] < MIN_CASES or counts[0] <= _threshold(usual):
            continue
        ages: dict[str, int] = {}
        for e in ws[0]:
            if e.get("band"):
                ages[e["band"]] = ages.get(e["band"], 0) + 1
        top = max(ages.items(), key=lambda kv: kv[1]) if ages else None
        confirmed = sum(1 for e in ws[0] if e.get("confirmed"))
        growth = counts[0] / counts[1] if counts[1] else None
        signals.append({
            "area": area, "syndrome": synd, "name": NAME[synd], "picture": PICTURE[synd],
            "this_week": counts[0], "usual": round(usual, 1), "weeks": counts[::-1],     # oldest first
            "confirmed": confirmed, "level": "confirmed" if confirmed >= CONFIRM_AT else "likely",
            "age": {"band": top[0], "count": top[1], "of": sum(ages.values())}
                   if top and top[1] / sum(ages.values()) >= AGE_SHARE and top[1] >= 3 else None,
            "next_week": min(round(counts[0] * min(growth, 2)), 999) if growth and growth > 1 else None,
        })
    signals.sort(key=lambda s: (s["level"] != "confirmed", -s["this_week"]))
    level = {a: "usual" for a in AREAS}
    for s in signals:
        if s["level"] == "confirmed" or level[s["area"]] == "usual":
            level[s["area"]] = s["level"]
    watch = {}
    for s in signals:
        if s["level"] == "confirmed":
            for n in neighbours(s["area"]):
                if level[n] == "usual":
                    level[n] = "watch"
                    watch[n] = f"Next to {s['area']}, where {s['name'].lower()} is confirmed"
    totals = {a: 0 for a in AREAS}
    for (area, _), ws in weeks.items():
        totals[area] += len(ws[0])
    return {"signals": signals, "now": now,
            "areas": [{"name": a, "level": level[a], "this_week": totals[a], "why": watch.get(a),
                       "clinic": a == CLINIC} for a in AREAS],
            "demo_history": any(e.get("demo") for e in STATE["events"]),
            "rule": {"min_cases": MIN_CASES, "confirm_at": CONFIRM_AT, "weeks": WEEKS - 1}}
