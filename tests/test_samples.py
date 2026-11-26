"""The made-up patients: the rules alone must already catch the worded emergencies."""

import json
from pathlib import Path

from app import prompts, triage

DATA = json.loads((Path(__file__).parent.parent / "samples" / "patients.json").read_text())


def said(p):
    return [p["opening"], *p["answers"].values()]


def test_every_patient_is_well_formed():
    ids = [p["id"] for p in DATA["patients"]]
    assert len(ids) == len(set(ids)) == 30
    for p in DATA["patients"]:
        assert p["lang"] in ("sn", "en") and p["expect"] in triage.LEVELS
        assert set(p["answers"]) <= set(prompts.TOPICS)


def test_rules_never_alarm_on_a_routine_patient():
    for p in DATA["patients"]:
        if p["expect"] == "routine":
            defaults = DATA["defaults"][p["lang"]].values()
            for line in [*said(p), *defaults]:
                assert triage.scan(line, p["lang"]) == [], (p["id"], line)


def test_rules_do_not_call_an_urgent_patient_an_emergency():
    for p in DATA["patients"]:
        if p["expect"] == "urgent":
            for line in said(p):
                assert all(r.level != "emergency" for r in triage.scan(line, p["lang"])), (p["id"], line)
