"""The national picture: where conditions favour an outbreak, province by province.

Three kinds of evidence are combined into a risk score from 0 to 100 for each province and
each of three illnesses. Every point of the score is shown with where it came from.

  WEATHER      real: rainfall and temperature for the last eight weeks and the coming week at
               each province's centre point, from Open-Meteo (CC BY 4.0). Refreshed every six
               hours; a dated copy in samples/weather_snapshot.json is used when it cannot be fetched.
  WATER        made up for the demonstration: how many water points clinics reported broken or
               unsafe. No open, current source for this was found.
  PAST CASES   made up for the demonstration: cases reported by clinics in each province over
               eight weeks. A real system would read the national weekly disease returns.

The weights are ours, set from general public-health reasoning (heavy rain and unsafe water
favour diarrhoeal disease; rain some weeks earlier and warmth favour malaria; cold favours
chest infections). They have not been fitted to data or reviewed by an epidemiologist, and the
score is a ranking aid, not a probability. No model computes any of it.
"""

from __future__ import annotations

import json
import random
import time

import httpx

from . import config

REFRESH_SECONDS = 6 * 3600
HIGH, WATCH = 60, 40
WEATHER: dict = {}

DISEASES = {
    "diarrhoeal": {"name": "Cholera and other diarrhoeal disease", "picture": "vomiting", "syndrome": "diarrhoea",
                   "advice": "Check stocks of oral rehydration salts and tell community health workers to promote boiled or treated water."},
    "malaria": {"name": "Malaria", "picture": "fever", "syndrome": "fever",
                "advice": "Check stocks of malaria tests and treatment, and expect more fever cases, in children first."},
    "respiratory": {"name": "Chest infections", "picture": "breathing", "syndrome": "breathing",
                    "advice": "Expect more coughs and breathing trouble, in small children and older people first."},
}
# Provinces where malaria is most established: our reading of general knowledge of the lowveld and
# the northern and eastern borders, to be replaced by the Ministry's own malaria stratification.
MALARIA_ZONE = {"Mashonaland Central": 1.0, "Manicaland": 1.0, "Matabeleland North": 0.8, "Mashonaland East": 0.7,
                "Masvingo": 0.7, "Mashonaland West": 0.6, "Matabeleland South": 0.5, "Midlands": 0.3,
                "Harare": 0.1, "Bulawayo": 0.1}


def provinces() -> list[dict]:
    return json.loads((config.WEB / "zw_provinces.json").read_text())["provinces"]


def _snapshot() -> dict:
    return json.loads((config.SAMPLES / "weather_snapshot.json").read_text())


def _cache():
    return config.DATA / "weather.json"


def weather() -> dict:
    """The newest weather we hold, without waiting for the network."""
    if WEATHER:
        return WEATHER
    try:
        WEATHER.update(json.loads(_cache().read_text()))
    except (OSError, ValueError):
        WEATHER.update({**_snapshot(), "live": False})
    return WEATHER


async def refresh(force: bool = False) -> bool:
    """Fetch the weather again if it is older than six hours. Never raises."""
    w = weather()
    if not force and w.get("live") and time.time() - w.get("fetched_at", 0) < REFRESH_SECONDS:
        return True
    ps = provinces()
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get("https://api.open-meteo.com/v1/forecast", params={
                "latitude": ",".join(str(p["lat"]) for p in ps), "longitude": ",".join(str(p["lon"]) for p in ps),
                "daily": "precipitation_sum,temperature_2m_mean", "past_days": 56, "forecast_days": 7,
                "timezone": "Africa/Harare"})
            r.raise_for_status()
            data = r.json()
        got = {"fetched": time.strftime("%Y-%m-%d"), "fetched_at": time.time(), "live": True, "past_days": 56,
               "source": _snapshot()["source"],
               "provinces": {p["name"]: {"time": x["daily"]["time"], "rain": x["daily"]["precipitation_sum"],
                                         "temp": x["daily"]["temperature_2m_mean"]} for p, x in zip(ps, data)}}
        WEATHER.clear()
        WEATHER.update(got)
        config.DATA.mkdir(parents=True, exist_ok=True)
        _cache().write_text(json.dumps(got))
        return True
    except Exception:
        return False


def conditions(name: str) -> dict:
    """What the weather has done and is forecast to do in one province."""
    w = weather()
    x, past = w["provinces"][name], w.get("past_days", 56)
    rain = [v or 0.0 for v in x["rain"]]
    temp = [v for v in x["temp"][:past] if v is not None]
    return {"rain_7": round(sum(rain[past - 7:past]), 1), "rain_next_7": round(sum(rain[past:past + 7]), 1),
            "rain_2_to_6_weeks_ago": round(sum(rain[past - 42:past - 14]), 1),
            "rain_30": round(sum(rain[past - 30:past]), 1),
            "temp_7": round(sum(temp[-7:]) / max(1, len(temp[-7:])), 1),
            "rain_by_week": [round(sum(rain[i:i + 7]), 1) for i in range(0, past, 7)]}


def made_up(now: float | None = None) -> dict:
    """The demonstration's water reports and case counts. Seeded by the week, so it is steady within one."""
    rng = random.Random(int((now or time.time()) // (7 * 86400)))
    out = {}
    rises = {("Manicaland", "diarrhoeal"): 3.2, ("Harare", "diarrhoeal"): 2.1, ("Mashonaland Central", "malaria"): 2.6,
             ("Masvingo", "malaria"): 1.6}
    for p in provinces():
        name = p["name"]
        cases = {}
        for dis, base in (("diarrhoeal", 40), ("malaria", 55), ("respiratory", 70)):
            scale = base * (0.5 + MALARIA_ZONE[name]) if dis == "malaria" else base * rng.uniform(0.6, 1.3)
            weeks = [max(0, round(scale * rng.uniform(0.8, 1.2))) for _ in range(8)]
            lift = rises.get((name, dis))
            if lift:
                weeks[5], weeks[6], weeks[7] = (round(weeks[5] * (1 + (lift - 1) * f)) for f in (0.3, 0.65, 1.0))
            cases[dis] = weeks
        out[name] = {"cases": cases, "water_reports": {"Manicaland": 9, "Harare": 7, "Midlands": 5}.get(name, rng.randrange(0, 4)),
                     "confirmed": [d for (n, d) in (("Manicaland", "diarrhoeal"),) if n == name]}
    return out


def _driver(label: str, value: str, points: float, most: int, source: str) -> dict:
    return {"label": label, "value": value, "points": round(min(most, max(0.0, points))), "max": most, "source": source}


def score(name: str, disease: str, c: dict, m: dict) -> dict:
    weeks = m["cases"][disease]
    recent, before = sum(weeks[-2:]) / 2, sum(weeks[:-2]) / 6
    growth = recent / before if before else 1.0
    cases = _driver("Cases in the last two weeks against the six before", f"{round(recent)} a week, was {round(before)}",
                    (growth - 1) * 30, 30, "made up")
    if disease == "diarrhoeal":
        d = [_driver("Rain in the last 7 days", f"{c['rain_7']} mm", c["rain_7"] / 80 * 30, 30, "weather"),
             _driver("Rain forecast for the next 7 days", f"{c['rain_next_7']} mm", c["rain_next_7"] / 60 * 15, 15, "weather"),
             _driver("Water points reported broken or unsafe", str(m["water_reports"]), m["water_reports"] / 8 * 25, 25, "made up"),
             cases]
    elif disease == "malaria":
        t = c["temp_7"]
        warm = 1.0 if 20 <= t <= 30 else 0.5 if 17 <= t <= 33 else 0.0
        zone = MALARIA_ZONE[name]
        d = [_driver("Rain two to six weeks ago, when mosquitoes breed", f"{c['rain_2_to_6_weeks_ago']} mm",
                     c["rain_2_to_6_weeks_ago"] / 120 * 30 * (0.4 + 0.6 * zone), 30, "weather"),
             _driver("Temperature this week", f"{t} °C", warm * 15, 15, "weather"),
             _driver("How established malaria is in this province", f"{round(zone * 100)}%", zone * 25, 25, "our estimate"),
             cases]
    else:
        t = c["temp_7"]
        d = [_driver("Temperature this week", f"{t} °C", (20 - t) / 10 * 45, 45, "weather"),
             _driver("Rain in the last 7 days", f"{c['rain_7']} mm", c["rain_7"] / 80 * 10, 10, "weather"),
             {**cases, "points": round(min(45, max(0.0, (growth - 1) * 45))), "max": 45}]
    total = min(100, sum(x["points"] for x in d))
    level = "confirmed" if disease in m["confirmed"] else "likely" if total >= HIGH else "watch" if total >= WATCH else "usual"
    return {"score": total, "level": level, "drivers": d, "cases_by_week": weeks}


def picture(now: float | None = None) -> dict:
    """Every province and illness, scored, with the warnings clinics should receive."""
    w, mu = weather(), made_up(now)
    rows = []
    for p in provinces():
        c = conditions(p["name"])
        m = mu[p["name"]]
        rows.append({"name": p["name"], "conditions": c, "water_reports": m["water_reports"],
                     "risk": {d: score(p["name"], d, c, m) for d in DISEASES}})
    order = ("confirmed", "likely", "watch")
    warnings = sorted(
        ({"province": r["name"], "disease": d, "name": DISEASES[d]["name"], "picture": DISEASES[d]["picture"],
          "level": r["risk"][d]["level"], "score": r["risk"][d]["score"], "advice": DISEASES[d]["advice"],
          "drivers": sorted(r["risk"][d]["drivers"], key=lambda x: -x["points"])}
         for r in rows for d in DISEASES if r["risk"][d]["level"] != "usual"),
        key=lambda x: (order.index(x["level"]), -x["score"]))
    return {"provinces": rows, "warnings": warnings,
            "diseases": {k: {"name": v["name"], "picture": v["picture"], "syndrome": v["syndrome"]} for k, v in DISEASES.items()},
            "weather": {"fetched": w.get("fetched"), "live": bool(w.get("live")), "source": w.get("source")},
            "thresholds": {"high": HIGH, "watch": WATCH}, "clinic_province": config.PROVINCE, "now": now or time.time()}


def for_clinic(now: float | None = None) -> list[dict]:
    """The warnings that apply to this clinic's own province."""
    return [w for w in picture(now)["warnings"] if w["province"] == config.PROVINCE]
