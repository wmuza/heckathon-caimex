"""Outbreak watch: the rule, the levels and what is kept. No network, no model."""

import pytest

from app import config, surveillance as sv, visits

NOW = 2_000_000_000.0
DAY = 86400


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    monkeypatch.setattr(config, "STORE", tmp_path / "sessions.json")
    monkeypatch.setattr(config, "AUDIO_DIR", tmp_path / "audio")
    visits.SESSIONS.clear()
    sv.STATE.clear()
    sv.STATE["events"] = []
    yield
    visits.SESSIONS.clear()
    sv.STATE.clear()


def cases(area, synd, per_week, band="13 to 27", confirmed=0):
    """per_week lists the counts from this week backwards."""
    for week, n in enumerate(per_week):
        for i in range(n):
            sv.STATE["events"].append({"at": NOW - week * 7 * DAY - DAY, "area": area, "syndrome": synd, "band": band,
                                       "confirmed": week == 0 and i < confirmed})


def level(area):
    return next(a["level"] for a in sv.analyse(NOW)["areas"] if a["name"] == area)


def test_a_rise_above_the_usual_is_a_signal():
    cases("Ward 3", "diarrhoea", [12, 2, 3, 2, 1])
    s = sv.analyse(NOW)["signals"][0]
    assert (s["area"], s["this_week"], s["usual"], s["level"], s["weeks"]) == ("Ward 3", 12, 2.0, "likely", [1, 2, 3, 2, 12])
    assert s["age"] == {"band": "13 to 27", "count": 12, "of": 12} and s["next_week"] == 24       # growth capped at doubling


def test_a_steady_week_or_a_handful_is_not_a_signal():
    cases("Ward 1", "fever", [6, 6, 5, 6, 6])          # busy but usual
    cases("Ward 2", "fever", [4, 0, 0, 0, 0])          # a rise, but under five cases
    assert sv.analyse(NOW)["signals"] == [] and level("Ward 1") == level("Ward 2") == "usual"


def test_three_diagnoses_by_the_doctor_make_it_confirmed_and_its_neighbours_are_watched():
    cases("Ward 3", "diarrhoea", [10, 1, 1, 1, 1], confirmed=3)
    assert level("Ward 3") == "confirmed"
    assert level("Ward 2") == level("Ward 6") == "watch"           # Ward 3 is a corner: two neighbours
    assert level("Ward 9") == "usual"
    sv.STATE["events"].clear()
    cases("Ward 3", "diarrhoea", [10, 1, 1, 1, 1], confirmed=2)
    assert level("Ward 3") == "likely" and level("Ward 2") == "usual"


def test_no_age_band_is_named_when_the_cases_are_spread():
    for b in ("under 5", "5 to 12", "13 to 27", "28 to 49", "50 and over"):
        cases("Ward 4", "fever", [2, 0, 0, 0, 0], band=b)
    assert sv.analyse(NOW)["signals"][0]["age"] is None


def test_age_bands_and_symptom_groups():
    assert sv.band({"value": 13, "unit": "years"}) == sv.band({"value": 27, "unit": "years"}) == "13 to 27"
    assert sv.band({"value": 8, "unit": "months"}) == "under 5" and sv.band(None) is None
    assert sv.syndrome("Diarrhoea since yesterday in a child") == "diarrhoea"
    assert sv.syndrome("Headache and cough for two days") == "breathing"
    assert sv.syndrome("Came to collect tablets") is None


def test_the_tally_keeps_no_name_no_words_and_no_ticket_number():
    s = visits.new("sn")
    s["status"] = "ready"
    s["turns"].append({"role": "user", "text": "Ndine manyoka kubva nezuro", "en": "I have had diarrhoea since yesterday"})
    visits.set_detail(s, "age", 19, "years")
    visits.set_detail(s, "area", "Ward 3")
    sv.sync(visits.SESSIONS)
    (row,) = sv.STATE["events"]
    assert set(row) == {"key", "at", "area", "syndrome", "band", "confirmed"}
    assert (row["area"], row["syndrome"], row["band"], row["confirmed"]) == ("Ward 3", "diarrhoea", "13 to 27", False)
    sv.sync(visits.SESSIONS)
    assert len(sv.STATE["events"]) == 1                              # the same visit is not counted twice


def test_sample_patients_and_visits_with_no_area_are_not_counted():
    a = visits.new("sn", sample="demo"); a["status"] = "ready"
    a["turns"].append({"role": "user", "text": "fever", "en": "fever"}); visits.set_detail(a, "area", "Ward 1")
    b = visits.new("sn"); b["status"] = "ready"; b["turns"].append({"role": "user", "text": "fever", "en": "fever"})
    sv.sync(visits.SESSIONS)
    assert sv.STATE["events"] == []


def test_the_starting_history_is_marked_made_up_and_shows_the_planted_rise():
    sv.STATE.clear()
    sv.load(NOW)
    assert all(e.get("demo") for e in sv.STATE["events"])
    out = sv.analyse(NOW)
    assert out["demo_history"] and (out["signals"][0]["area"], out["signals"][0]["level"]) == ("Ward 3", "confirmed")
    assert {a["name"]: a["level"] for a in out["areas"]}["Ward 6"] == "likely"
