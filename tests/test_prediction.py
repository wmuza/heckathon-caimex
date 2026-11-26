"""The clinic forecaster and the national picture. No network, no model."""

import json

import pytest

from app import config, national, prediction as pr, surveillance as sv, voice

DN0 = 20_000


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    sv.STATE.clear(); national.WEATHER.clear()
    yield
    sv.STATE.clear(); national.WEATHER.clear()


def flat(rate=1, last7=None, n=92):
    """k days ago -> count: a steady series, with the last seven complete days optionally replaced."""
    c = [rate] * n
    for k, v in enumerate(last7 or [], start=1):
        c[k] = v
    return c


PROF = [1.0] * 7


def test_the_usual_is_learnt_from_days_15_to_70_ago_so_a_rise_does_not_become_the_usual():
    c = flat(1, last7=[9] * 7)
    for k in range(8, 15):
        c[k] = 9                                             # two weeks of outbreak already
    assert pr.usual_rate(c, 0) == 1.0
    assert pr.detect(c, 0, PROF, DN0)["usual"] == pytest.approx(7.0)


def test_a_clear_rise_is_flagged_and_a_steady_week_is_not():
    up = pr.detect(flat(1, last7=[4] * 7), 0, PROF, DN0)
    assert up["seen"] == 28 and up["alert"] and up["z"] == pytest.approx((28 - 7) / 8 ** 0.5)
    assert not pr.detect(flat(1), 0, PROF, DN0)["alert"]
    assert not pr.detect(flat(0, last7=[1, 1, 1, 0, 0, 0, 0]), 0, PROF, DN0)["alert"]      # three cases: too few


def test_as_of_a_past_day_only_what_was_known_then_is_used():
    c = flat(1, last7=[6] * 7)
    assert pr.detect(c, 0, PROF, DN0)["alert"] and not pr.detect(c, 7, PROF, DN0)["alert"]


def test_the_weekday_pattern_is_the_clinics_own():
    total = [0] * 92
    for k in range(92):
        total[k] = 10 if pr.weekday(DN0 - k) == 0 else 2          # Mondays are five times as busy
    prof = pr.profile(total, 0, DN0)
    assert prof[0] > 3 and prof[2] < 1 and sum(prof) / 7 == pytest.approx(1, abs=0.35)
    assert pr.weekday(pr.day_number(0)) == 3                  # 1 January 1970 was a Thursday


def test_the_forecast_stays_near_the_usual_in_a_calm_week_and_moves_in_a_strong_rise():
    calm = pr.forecast(flat(1), 0, PROF, DN0)
    assert calm["mean"] == pytest.approx(7.0) and calm["lo"] < 7 < calm["hi"] and not calm["strong"]
    rise = pr.forecast(flat(1, last7=[5] * 7), 0, PROF, DN0)
    assert rise["strong"] and 7 < rise["mean"] < 35                       # above the usual, below "same as this week"
    assert rise["hi"] - rise["lo"] > calm["hi"] - calm["lo"]              # and less sure of itself


def test_the_settings_are_the_ones_the_scoring_run_chose():
    r = json.loads((config.EVAL / "prediction_results.json").read_text())
    s = r["settings"]
    assert (s["z_alert"], s["calm"], s["rise"], s["phi"], s["kappa"]) == (
        pr.Z_ALERT, list(pr.CALM), list(pr.RISE), pr.PHI, pr.KAPPA)
    assert r["clinics"]["test"] >= 20 and "Not real patients" in r["about"]


def test_on_the_made_up_history_the_planted_rise_is_found_with_a_range_and_a_stock_date():
    sv.load(1_795_700_000.0)
    shelf = [{"id": "ors", "name": "Oral rehydration salts", "unit": "sachets", "stock": 420, "per_day": 9.4}]
    p = pr.predict(1_795_700_000.0, shelf)
    top = p["signals"][0]
    assert (top["area"], top["syndrome"], top["level"]) == ("Ward 3", "diarrhoea", "confirmed")
    assert top["next7"]["lo"] <= top["next7"]["mean"] <= top["next7"]["hi"] and top["next7"]["mean"] > top["usual"]
    assert len(top["days"]) == 28 and len(top["ahead"]) == 7 and top["stock"]["med"] == "ors"
    levels = {a["name"]: a["level"] for a in p["areas"]}
    assert levels["Ward 3"] == "confirmed" and levels["Ward 2"] == "watch"
    assert len(p["replay"]) == pr.REPLAY_DAYS + 1 and p["replay"][-1]["levels"]["Ward 3"] == "likely"
    assert all(t["lo"] <= t["expected"] <= t["hi"] for t in p["today"]) and p["demo_history"]
    assert pr.stock_days(420, 9.4, 0, 3) == pytest.approx(44.7, abs=0.1) and pr.stock_days(420, 9.4, 4, 3) < 20


def test_a_doctors_diagnosis_confirms_only_its_own_kind_of_illness():
    assert sv.syndrome("Cholera") == "diarrhoea" and sv.syndrome("Sprained ankle") is None


def test_the_national_score_shows_every_point_and_where_it_came_from():
    p = national.picture(1_795_700_000.0)
    assert len(p["provinces"]) == 10 and p["weather"]["source"].startswith("Open-Meteo")
    for r in p["provinces"]:
        for d, x in r["risk"].items():
            assert 0 <= x["score"] <= 100 and x["score"] == min(100, sum(k["points"] for k in x["drivers"]))
            assert all(k["source"] in ("weather", "made up", "our estimate") and 0 <= k["points"] <= k["max"] for k in x["drivers"])
    assert p["warnings"] and all(w["level"] != "usual" for w in p["warnings"])
    assert [w["level"] for w in p["warnings"]] == sorted((w["level"] for w in p["warnings"]),
                                                         key=("confirmed", "likely", "watch").index)


def test_more_rain_and_unsafe_water_raise_the_diarrhoeal_score():
    m = {"cases": {"diarrhoeal": [40] * 8}, "water_reports": 0, "confirmed": []}
    dry = {"rain_7": 0, "rain_next_7": 0, "rain_2_to_6_weeks_ago": 0, "temp_7": 24}
    wet = {**dry, "rain_7": 90, "rain_next_7": 60}
    a, b = national.score("Harare", "diarrhoeal", dry, m)["score"], national.score("Harare", "diarrhoeal", wet, m)["score"]
    c = national.score("Harare", "diarrhoeal", wet, {**m, "water_reports": 8})["score"]
    assert a == 0 and b == 45 and c == 70
    assert national.score("Harare", "diarrhoeal", wet, {**m, "water_reports": 8})["level"] == "likely"


def test_a_clinic_gets_only_its_own_provinces_warnings(monkeypatch):
    monkeypatch.setattr(config, "PROVINCE", "Manicaland")
    mine = national.for_clinic(1_795_700_000.0)
    assert mine and all(w["province"] == "Manicaland" for w in mine)


def test_the_spoken_briefing_says_the_numbers_on_the_screen():
    sv.load(1_795_700_000.0)
    p = pr.predict(1_795_700_000.0)
    text = voice.briefing_text(p, national.for_clinic(1_795_700_000.0))
    t = p["today"][0]
    assert f"about {t['expected']} patients" in text and "Ward 3" in text and "National warning" in text
