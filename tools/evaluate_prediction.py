"""Score the clinic forecaster on simulated clinics where the truth is known. Writes eval/prediction_results.json.

  uv run python tools/evaluate_prediction.py

There is no openly licensed ward-level clinic series for Zimbabwe that we know of, and no real
patient data may be used, so the clinics here are simulated: nine wards and three symptom groups,
fourteen months of daily visits with a weekday pattern, a slow seasonal swing, more scatter than
chance alone gives, a few closed days, and outbreaks planted at known days and sizes.

Two sets of clinics are made from different random seeds. The first is used to choose the
settings (the alert threshold, the forecast's pull and damping, the width of its range). The
second is only scored. Detection is replayed day by day using only what was known that day.

What this shows: how the arithmetic in app/prediction.py behaves against a simple weekly count
and against "next week will be like this week", on outbreaks shaped the way we chose to shape
them. What it does not show: how it does on real outbreaks. The simulator was written by the
same hand as the detector.
"""

from __future__ import annotations

import json
import math
import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import prediction as pr  # noqa: E402

DAYS, WARM = 420, 100
TUNE_SEEDS, TEST_SEEDS = range(1, 13), range(101, 131)
WEEK = (1.35, 1.15, 1.05, 1.0, 0.95, 0.5, 0.3)
WITHIN = 14                      # an outbreak counts as caught if flagged within this many days of its start


def poisson(rng: random.Random, lam: float) -> int:
    if lam <= 0:
        return 0
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def clinic(seed: int) -> dict:
    """One simulated clinic: 27 daily series, oldest day first, and where its outbreaks are."""
    rng = random.Random(seed)
    closed = set(rng.sample(range(DAYS), 5))
    series, outbreaks = [], []
    for i in range(27):
        base = rng.uniform(0.15, 0.9)
        phase = rng.uniform(0, 2 * math.pi)
        plan = None
        if rng.random() < 0.3:
            start = rng.randrange(150, DAYS - 50)
            plan = {"series": i, "start": start, "length": rng.randrange(18, 36),
                    "peak": max(0.8, base * rng.choice((2, 3, 5))), "gradual": rng.random() < 0.3}
            outbreaks.append(plan)
        days = []
        for t in range(DAYS):
            lam = base * WEEK[t % 7] * (1 + 0.25 * math.sin(2 * math.pi * t / 365 + phase))
            if plan and plan["start"] <= t < plan["start"] + plan["length"]:
                x = (t - plan["start"]) / plan["length"]
                rise = 0.7 if plan["gradual"] else 0.35
                lam += plan["peak"] * (x / rise if x < rise else (1 - x) / (1 - rise))
            lam *= rng.gammavariate(4, 0.25)                      # more scatter than Poisson alone
            days.append(0 if t in closed else poisson(rng, lam))
        series.append(days)
    return {"series": series, "outbreaks": outbreaks}


def replay(c: dict) -> list[dict]:
    """For every series and day: the detector's z, whether the weekly rule fires, and forecasts to score."""
    last = DAYS - 1
    dn0 = 7000 + last                                   # so that day t falls on weekday (t + 7000 + 3) % 7
    rev = [s[::-1] for s in c["series"]]
    total = [sum(col) for col in zip(*rev)]
    out = []
    for t in range(WARM, DAYS):
        o = last - t
        prof = pr.profile(total, o, dn0)
        for i, r in enumerate(rev):
            d = pr.detect(r, o, prof, dn0)
            out.append({"i": i, "t": t, "z": d["z"], "seen": d["seen"], "weekly": pr.weekly_rule(r, o)})
    return out


def episodes(days: list[int]) -> list[list[int]]:
    runs = []
    for t in days:
        if runs and t - runs[-1][-1] <= 7:
            runs[-1].append(t)
        else:
            runs.append([t])
    return runs


def score_detection(clinics: list[dict], rows: list[list[dict]], fires) -> dict:
    caught, delays, total, false_eps, quiet_days = 0, [], 0, 0, 0
    for c, rr in zip(clinics, rows):
        by = {}
        for r in rr:
            if fires(r):
                by.setdefault(r["i"], []).append(r["t"])
        plan = {o["series"]: o for o in c["outbreaks"]}
        for i in range(len(c["series"])):
            o = plan.get(i)
            alerts = by.get(i, [])
            quiet_days += (DAYS - WARM) - (o["length"] + 7 if o else 0)
            if o:
                total += 1
                hit = next((t for t in alerts if o["start"] <= t <= o["start"] + WITHIN), None)
                if hit is not None:
                    caught += 1
                    delays.append(hit - o["start"])
            for ep in episodes(alerts):
                if not o or ep[-1] < o["start"] or ep[0] > o["start"] + o["length"] + 7:
                    false_eps += 1
    return {"outbreaks": total, "caught_within_14_days": caught,
            "median_days_to_flag": statistics.median(delays) if delays else None,
            "false_alarms_per_ward_year": round(false_eps / (quiet_days / 365), 2)}


def forecast_errors(clinics: list[dict], calm=None, rise=None) -> list[dict]:
    last = DAYS - 1
    dn0 = 7000 + last
    out = []
    for c in clinics:
        rev = [s[::-1] for s in c["series"]]
        total = [sum(col) for col in zip(*rev)]
        plan = {o["series"]: o for o in c["outbreaks"]}
        for t in range(WARM, DAYS - 7, 7):
            o = last - t
            prof = pr.profile(total, o, dn0)
            for i, r in enumerate(rev):
                f = pr.forecast(r, o, prof, dn0, 7, calm, rise)
                truth = sum(r[o - 6:o + 1])
                p = plan.get(i)
                out.append({"mean": f["mean"], "truth": truth, "same_as_last_week": sum(r[o + 1:o + 8]), "usual": f["usual"], "flagged": f["flagged"], "strong": f["strong"],
                            "surge": bool(p and p["start"] <= t + 3 <= p["start"] + p["length"])})
    return out


def mae(rows, key):
    return round(statistics.mean(abs(r[key] - r["truth"]) for r in rows), 3) if rows else None


def coverage(rows, phi, kappa=0.0):
    inside = 0
    for r in rows:
        lo, hi = pr.spread(r["mean"], phi, r["usual"], kappa)
        inside += math.floor(lo) <= r["truth"] <= math.ceil(hi)
    return round(inside / len(rows), 3)


def main() -> None:
    t0 = time.time()
    tune = [clinic(s) for s in TUNE_SEEDS]
    test = [clinic(s) for s in TEST_SEEDS]
    tune_rows, test_rows = [replay(c) for c in tune], [replay(c) for c in test]

    # 1. The alert threshold, by a rule written before the run: the fewest false alarms while still
    #    catching at least nine in ten of the outbreaks the weekly count catches, on the tuning clinics.
    weekly_tune = score_detection(tune, tune_rows, lambda r: r["weekly"])
    curve = {z: score_detection(tune, tune_rows, lambda r, z=z: r["z"] >= z and r["seen"] >= pr.MIN_WEEK)
             for z in [x / 4 for x in range(4, 17)]}
    z = max(z for z, sc in curve.items() if sc["caught_within_14_days"] >= 0.9 * weekly_tune["caught_within_14_days"])

    # 2. The forecast's settings: the lowest error on the tuning clinics.
    #    One setting for ordinary weeks and one for a strong rise (z of 4 or more, known that day, not hindsight).
    grid = [(n, p, d) for n in (7, 14) for p in (0.5, 1.0, 2.0, 4.0) for d in (0.6, 0.8, 1.0, 1.2)]
    tried = {g: forecast_errors(tune, g, g) for g in grid}
    calm = min(grid, key=lambda g: mae([r for r in tried[g] if not r["strong"]], "mean"))
    rise = min(grid, key=lambda g: mae([r for r in tried[g] if r["strong"]], "mean"))
    tune_f = forecast_errors(tune, calm, rise)
    steady = [r for r in tune_f if not r["surge"]]
    phi = next(p / 10 for p in range(4, 60) if coverage(steady, p / 10) >= 0.80)
    # During a rise the forecast lags, so no reasonable widening reaches 80% there. Widen as far as
    # 70% inside during outbreaks on the tuning clinics, and never beyond 1.5; the test score says what was reached.
    rising = [r for r in tune_f if r["surge"]]
    kappa = next((k / 10 for k in range(0, 16) if coverage(rising, phi, k / 10) >= 0.70), 1.5)

    # 3. Score on clinics the settings never saw.
    test_f = forecast_errors(test, calm, rise)
    surge, quiet = [r for r in test_f if r["surge"]], [r for r in test_f if not r["surge"]]
    flagged = [r for r in test_f if r["flagged"]]
    out = {
        "ran_at": time.strftime("%Y-%m-%d %H:%M"),
        "about": "Simulated clinics with planted outbreaks; see the top of tools/evaluate_prediction.py. Not real patients, "
                 "and not validation on real outbreaks. Settings were chosen on the tuning clinics and scored on the test clinics.",
        "clinics": {"tuning": len(tune), "test": len(test), "series_each": 27, "days_scored_each": DAYS - WARM},
        "settings": {"z_alert": z, "min_week": pr.MIN_WEEK, "calm": list(calm), "rise": list(rise), "phi": phi, "kappa": kappa},
        "detection_test": {
            "this_detector": score_detection(test, test_rows, lambda r: r["z"] >= z and r["seen"] >= pr.MIN_WEEK),
            "weekly_count": score_detection(test, test_rows, lambda r: r["weekly"])},
        "detection_tuning": {"weekly_count": weekly_tune, "this_detector_by_threshold": curve,
                             "rule": "fewest false alarms while catching at least 9 in 10 of what the weekly count catches"},
        "forecast_test": {
            "weeks_scored": len(test_f),
            "mean_error_cases_a_week": {"this_forecast": mae(test_f, "mean"), "same_as_last_week": mae(test_f, "same_as_last_week"),
                                        "the_usual": mae(test_f, "usual")},
            "during_outbreaks": {"weeks": len(surge), "this_forecast": mae(surge, "mean"),
                                 "same_as_last_week": mae(surge, "same_as_last_week"), "the_usual": mae(surge, "usual")},
            "weeks_flagged_by_the_detector": {"weeks": len(flagged), "this_forecast": mae(flagged, "mean"),
                                              "same_as_last_week": mae(flagged, "same_as_last_week"), "the_usual": mae(flagged, "usual")},
            "quiet_weeks": {"weeks": len(quiet), "this_forecast": mae(quiet, "mean"),
                            "same_as_last_week": mae(quiet, "same_as_last_week"), "the_usual": mae(quiet, "usual")},
            "share_of_weeks_inside_the_80_range": coverage(test_f, phi, kappa),
            "inside_the_range_during_outbreaks": coverage(surge, phi, kappa) if surge else None},
        "seconds": round(time.time() - t0),
    }
    path = ROOT / "eval" / "prediction_results.json"
    path.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    s = out["settings"]
    now = {"z_alert": pr.Z_ALERT, "calm": list(pr.CALM), "rise": list(pr.RISE), "phi": pr.PHI, "kappa": pr.KAPPA}
    if any(now[k] != s[k] for k in now):
        print("\nThe settings in app/prediction.py differ from the ones chosen here:", now, "->",
              {k: s[k] for k in now}, "\nChange them there and run this again so the two agree.")


if __name__ == "__main__":
    main()
