"""Prediction for one clinic: what to expect today, where an illness is rising, and what next week holds.

Plain statistics, written out so it can be checked and scored. No model computes a number here.
CAIMEx models explain, speak and draft from these numbers (app/ai.py); they never produce them.

For each ward and symptom group:

  USUAL     the ward's mean visits a day over eight earlier weeks (days 15 to 70 ago), times the
            clinic's weekday pattern. The last two weeks are left out so that an outbreak which
            has already begun does not become "the usual".
  DETECT    the last seven complete days against the usual for those days:
            z = (seen - usual) / sqrt(usual + 1). An unusual rise is flagged at z >= Z_ALERT with
            at least MIN_WEEK cases.
  FORECAST  the usual for each coming day, times how far recent days ran above or below their own
            usual (pulled toward 1 when counts are small, and damped; less so once a rise is flagged). The range
            is the middle 80%: the forecast give or take 1.28 * sqrt(PHI * forecast), widened by
            KAPPA times its distance from the usual.

Z_ALERT and PHI were chosen on simulated clinics with planted outbreaks and then scored on
simulated clinics they had not seen (tools/evaluate_prediction.py, eval/prediction_results.json).
That is evidence the arithmetic behaves; it is not validation on real outbreaks.
"""

from __future__ import annotations

import math
import time

from . import surveillance as sv

DAY = 86400
BASE_FROM, BASE_TO = 15, 70     # the usual is learnt from days 15 to 70 ago
Z_ALERT = 2.0                   # set by tools/evaluate_prediction.py; see eval/prediction_results.json
Z_WATCH = 1.5
MIN_WEEK = 4
PHI = 0.5                       # spread of the forecast range, from the same run
KAPPA = 1.5                     # extra width when the forecast is far from the usual, from the same run
CALM = (14, 4.0, 0.6)           # forecast settings in an ordinary week: (recent days, pull toward the usual, damping)
RISE = (7, 1.0, 0.6)            # and in a strong rise (z >= Z_STRONG); both from the same run
Z_STRONG = 4.0
REPLAY_DAYS = 21
CONFIRM_AT = sv.CONFIRM_AT

# What an extra case draws from the shelf: a planning assumption a pharmacist can change on the page,
# not a treatment rule. (symptom group -> medicine id, units per extra case)
DRAWS = {"diarrhoea": ("ors", 3), "fever": ("paracetamol", 12), "breathing": ("amoxicillin", 15)}


def day_number(t: float) -> int:
    return int((t + 7200) // DAY)           # days are Harare days (UTC+2)


def weekday(dn: int) -> int:
    return (dn + 3) % 7                      # Monday is 0


def profile(total: list[int], o: int, dn0: int) -> list[float]:
    """The clinic's weekday pattern as of `o` days ago: seven multipliers that average 1.
    `total[k]` is every visit k days ago; dn0 is today's day number."""
    sums, days = [0.0] * 7, [0] * 7
    for k in range(o + BASE_FROM, min(o + BASE_TO, len(total) - 1) + 1):
        w = weekday(dn0 - k)
        sums[w] += total[k]
        days[w] += 1
    mean = sum(sums) / max(1, sum(days))
    if mean <= 0:
        return [1.0] * 7
    return [((sums[w] / days[w]) / mean) if days[w] else 1.0 for w in range(7)]


def usual_rate(c: list[int], o: int) -> float:
    """Mean visits a day over the learning window, as of `o` days ago."""
    window = c[o + BASE_FROM:o + BASE_TO + 1]
    return sum(window) / len(window) if window else 0.0


def detect(c: list[int], o: int, prof: list[float], dn0: int) -> dict:
    rate = usual_rate(c, o)
    seen = sum(c[o + 1:o + 8])
    usual = sum(rate * prof[weekday(dn0 - k)] for k in range(o + 1, o + 8))
    z = (seen - usual) / math.sqrt(usual + 1)
    return {"seen": seen, "usual": usual, "z": z, "alert": z >= Z_ALERT and seen >= MIN_WEEK,
            "watch": z >= Z_WATCH and seen >= MIN_WEEK}


def spread(mean: float, phi: float | None = None, usual: float | None = None, kappa: float | None = None) -> tuple[float, float]:
    """The middle 80% around a forecast. Wider when the forecast is far from the usual, because
    a rising count is harder to call than a steady one."""
    phi = PHI if phi is None else phi
    kappa = KAPPA if kappa is None else kappa
    half = 1.28 * math.sqrt(phi * max(mean, 0.25)) + (kappa * abs(mean - usual) if usual is not None else 0)
    return max(0.0, mean - half), mean + half


def forecast(c: list[int], o: int, prof: list[float], dn0: int, days: int = 7,
             calm: tuple | None = None, rise: tuple | None = None) -> dict:
    """The coming `days` days, counting the day `o` days ago as the first. Mean and the middle 80%.

    Two settings, each (recent days, pull, damping): CALM in an ordinary week, where most ups and
    downs are chance and the forecast stays near the usual; RISE in a strong rise, where the last
    week counts for more. Both are damped: on the simulated clinics a spike was usually followed by
    a lower week, so "next week will be like this week" did worse than either."""
    d = detect(c, o, prof, dn0)
    flagged, strong = d["alert"], d["z"] >= Z_STRONG and d["seen"] >= MIN_WEEK
    n, pull, damp = (rise or RISE) if strong else (calm or CALM)
    rate = usual_rate(c, o)
    seen = sum(c[o + 1:o + 1 + n])
    usual_n = sum(rate * prof[weekday(dn0 - k)] for k in range(o + 1, o + 1 + n))
    ratio = max(0.0, 1 + ((seen + pull) / (usual_n + pull) - 1) * damp)
    daily = [rate * prof[weekday(dn0 - o + j)] * ratio for j in range(days)]
    usual = [rate * prof[weekday(dn0 - o + j)] for j in range(days)]
    mean = sum(daily)
    lo, hi = spread(mean, usual=sum(usual))
    return {"mean": mean, "lo": lo, "hi": hi, "usual": sum(usual), "ratio": ratio, "daily": daily,
            "usual_daily": usual, "flagged": flagged, "strong": strong}


def weekly_rule(c: list[int], o: int) -> bool:
    """The simple weekly count this is compared with (surveillance.analyse, taken day by day)."""
    weeks = [sum(c[o + 1 + 7 * w:o + 8 + 7 * w]) for w in range(sv.WEEKS)]
    usual = sum(weeks[1:]) / (sv.WEEKS - 1)
    return weeks[0] >= sv.MIN_CASES and weeks[0] > usual + 2 * math.sqrt(usual)


# ── From the tally ─────────────────────────────────────────────────────────

def series(now: float) -> tuple[dict, list[int], int, dict]:
    """Daily counts by (ward, symptom group), k days ago; the clinic total; today's day number;
    and this week's rows for ages and diagnoses."""
    if not sv.STATE:
        sv.load()
    dn0 = day_number(now)
    n = sv.HISTORY_DAYS + 1
    counts: dict[tuple[str, str], list[int]] = {}
    total = [0] * n
    recent: dict[tuple[str, str], list[dict]] = {}
    for e in sv.STATE["events"]:
        k = dn0 - day_number(e["at"])
        if 0 <= k < n:
            key = (e["area"], e["syndrome"])
            counts.setdefault(key, [0] * n)[k] += 1
            total[k] += 1
            if 1 <= k <= 7:
                recent.setdefault(key, []).append(e)
    return counts, total, dn0, recent


def _level(d: dict, diagnosed: int) -> str:
    return "confirmed" if d["alert"] and diagnosed >= CONFIRM_AT else "likely" if d["alert"] else "usual"


def _first(c: list[int], test, days: int = REPLAY_DAYS) -> int | None:
    """How many days ago a test first held, in the unbroken run that reaches today."""
    first = None
    for o in range(0, days + 1):
        if test(o):
            first = o
        elif first is not None:
            break
    return first


def predict(now: float | None = None, shelf: list[dict] | None = None) -> dict:
    now = now or time.time()
    counts, total, dn0, recent = series(now)
    prof = profile(total, 0, dn0)
    signals, level, watch_why = [], {a: "usual" for a in sv.AREAS}, {}
    week_total = {a: 0 for a in sv.AREAS}
    today: dict[str, dict] = {s: {"mean": 0.0, "usual": 0.0} for s in sv.NAME}
    for (area, synd), c in sorted(counts.items()):
        d = detect(c, 0, prof, dn0)
        f = forecast(c, 0, prof, dn0)
        week_total[area] += d["seen"]
        today[synd]["mean"] += f["daily"][0]
        today[synd]["usual"] += f["usual_daily"][0]
        if not (d["alert"] or d["watch"]):
            continue
        rows = recent.get((area, synd), [])
        ages: dict[str, int] = {}
        for e in rows:
            if e.get("band"):
                ages[e["band"]] = ages.get(e["band"], 0) + 1
        top = max(ages.items(), key=lambda kv: kv[1]) if ages else None
        diagnosed = sum(1 for e in rows if e.get("confirmed"))
        lv = _level(d, diagnosed) if d["alert"] else "watch"
        sig = {
            "area": area, "syndrome": synd, "name": sv.NAME[synd], "picture": sv.PICTURE[synd], "level": lv,
            "seen": d["seen"], "usual": round(d["usual"], 1), "z": round(d["z"], 1), "diagnosed": diagnosed,
            "age": {"band": top[0], "count": top[1], "of": sum(ages.values())}
                   if top and top[1] / sum(ages.values()) >= sv.AGE_SHARE and top[1] >= 3 else None,
            "next7": {"mean": round(f["mean"]), "lo": round(f["lo"]), "hi": round(f["hi"]), "usual": round(f["usual"], 1)},
            "days": c[28:0:-1],                                  # the last 28 complete days, oldest first
            "usual_days": [round(usual_rate(c, 0) * prof[weekday(dn0 - k)], 2) for k in range(28, 0, -1)],
            "ahead": [round(x, 2) for x in f["daily"]], "ahead_usual": [round(x, 2) for x in f["usual_daily"]],
            "flagged_days_ago": _first(c, lambda o: detect(c, o, profile(total, o, dn0), dn0)["alert"]),
            "weekly_rule_days_ago": _first(c, lambda o: weekly_rule(c, o)),
        }
        draw = DRAWS.get(synd)
        med = next((m for m in shelf or [] if draw and m["id"] == draw[0]), None)
        if med and lv != "watch":
            extra = max(0.0, f["mean"] - f["usual"]) / 7
            sig["stock"] = {"med": med["id"], "name": med["name"], "unit": med["unit"], "left": med["stock"],
                            "per_day": med["per_day"], "extra_cases_a_day": round(extra, 1), "units_per_case": draw[1]}
        signals.append(sig)
        order = ("usual", "watch", "likely", "confirmed")
        if order.index(lv) > order.index(level[area]):
            level[area] = lv
    for s in signals:
        if s["level"] == "confirmed":
            for nb in sv.neighbours(s["area"]):
                if level[nb] == "usual":
                    level[nb] = "watch"
                    watch_why[nb] = f"Next to {s['area']}, where {s['name'].lower()} is confirmed"
    signals.sort(key=lambda s: (("confirmed", "likely", "watch").index(s["level"]), -s["z"]))
    tiles = []
    for synd, t in today.items():
        lo, hi = spread(t["mean"], usual=t["usual"])
        tiles.append({"syndrome": synd, "name": sv.NAME[synd], "picture": sv.PICTURE[synd],
                      "expected": round(t["mean"]), "lo": round(lo), "hi": round(hi), "usual": round(t["usual"], 1),
                      "above": t["mean"] >= 1.25 * t["usual"] and t["mean"] - t["usual"] >= 1})
    tiles.sort(key=lambda t: -t["expected"])
    return {
        "now": now, "weekday": ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")[weekday(dn0)],
        "today": [t for t in tiles if t["expected"] or t["usual"] >= 0.5],
        "signals": signals,
        "areas": [{"name": a, "level": level[a], "this_week": week_total[a], "why": watch_why.get(a),
                   "clinic": a == sv.CLINIC} for a in sv.AREAS],
        "replay": replay(counts, total, dn0),
        "demo_history": any(e.get("demo") for e in sv.STATE["events"]),
        "method": {"z_alert": Z_ALERT, "min_week": MIN_WEEK, "confirm_at": CONFIRM_AT, "phi": PHI, "kappa": KAPPA,
                   "learn_from": [BASE_FROM, BASE_TO]},
    }


def replay(counts: dict, total: list[int], dn0: int, days: int = REPLAY_DAYS) -> list[dict]:
    """The map as it would have stood on each of the last `days` days, using only what was known
    that day, by this detector and by the simple weekly count. Oldest day first."""
    frames = []
    for o in range(days, -1, -1):
        prof = profile(total, o, dn0)
        new, old = {a: "usual" for a in sv.AREAS}, {a: False for a in sv.AREAS}
        for (area, _), c in counts.items():
            if detect(c, o, prof, dn0)["alert"]:
                new[area] = "likely"
            if weekly_rule(c, o):
                old[area] = True
        frames.append({"ago": o, "levels": new, "weekly": old})
    return frames


def stock_days(left: float, per_day: float, extra_cases: float, units: float) -> float | None:
    use = per_day + extra_cases * units
    return left / use if use > 0 else None
