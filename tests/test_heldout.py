"""No emergency in eval/heldout.json may be missed by the rules alone.

The set is no longer held out: the rules were extended from what they missed on
it (eval/heldout_results.json). It is kept as a floor instead. If this fails, a
change to the patterns has lost an emergency they used to catch.
"""

import json

import pytest

from app import config, triage

ITEMS = json.loads((config.EVAL / "heldout.json").read_text())["items"]
EMERGENCIES = [i for i in ITEMS if i["expect"] == "emergency"]


def test_the_set_still_has_its_emergencies():
    assert len(EMERGENCIES) == 24


@pytest.mark.parametrize("item", EMERGENCIES, ids=[i["id"] for i in EMERGENCIES])
def test_every_emergency_is_found_by_the_rules_alone(item):
    found = triage.scan(item["text"], item["lang"])
    assert triage.highest([r.level for r in found]) == "emergency", item["text"]
