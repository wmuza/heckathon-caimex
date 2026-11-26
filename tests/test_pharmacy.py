"""Stock, dispensing and the supervisor's approvals. No network, no model."""

import pytest
from fastapi.testclient import TestClient

from app import config, pharmacy, server, visits

PIN = "2468"
DAY = 86400


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    monkeypatch.setattr(config, "STORE", tmp_path / "sessions.json")
    monkeypatch.setattr(config, "AUDIO_DIR", tmp_path / "audio")
    monkeypatch.setattr(config, "SUPERVISOR_PIN", PIN)
    monkeypatch.setattr(config, "NURSE_PIN", "")
    visits.SESSIONS.clear()
    server.WRONG_PINS.clear()
    pharmacy.load()
    yield
    visits.SESSIONS.clear()
    pharmacy.STATE.clear()


def stock(mid):
    return pharmacy._med(mid)["stock"]


def test_the_starting_history_is_marked_as_made_up():
    assert pharmacy.STATE["log"] and all(r.get("demo") for r in pharmacy.STATE["log"])


def test_days_left_is_stock_over_the_fortnights_use():
    pharmacy.STATE["medicines"] = [{"id": "x", "name": "X", "unit": "tablets", "stock": 300}]
    now = 1_000_000.0
    pharmacy.STATE["log"] = [{"at": now - d * DAY - 60, "kind": "dispense", "med": "x", "qty": -20} for d in range(14)] \
        + [{"at": now - 20 * DAY, "kind": "dispense", "med": "x", "qty": -999}]      # older than a fortnight: not counted
    m = pharmacy.forecast(now)[0]
    assert (m["per_day"], m["days_left"], m["status"]) == (20.0, 15, "soon")
    pharmacy.STATE["medicines"][0]["stock"] = 200
    assert pharmacy.forecast(now)[0]["status"] == "now"            # 10 days: under two weeks
    pharmacy.STATE["medicines"][0]["stock"] = 600
    assert pharmacy.forecast(now)[0]["status"] == "enough"         # 30 days: past four weeks
    pharmacy.STATE["medicines"][0]["stock"] = 0
    assert pharmacy.forecast(now)[0]["status"] == "none"


def test_a_medicine_nobody_uses_is_not_flagged():
    pharmacy.STATE["log"] = []
    assert all(m["days_left"] is None and m["status"] == "enough" for m in pharmacy.forecast())


def test_dispensing_takes_from_the_shelf_and_is_tied_to_the_ticket():
    before = stock("amlodipine")
    row = pharmacy.dispense("abc", 7, "amlodipine", 30, allowed=30, diagnosis="High blood pressure")
    assert stock("amlodipine") == before - 30 and row["ticket"] == 7 and not row.get("approved")
    assert pharmacy.forecast()[0] is not None and next(m for m in pharmacy.forecast() if m["id"] == "amlodipine")["for"] == ["High blood pressure"]


@pytest.mark.parametrize("qty", [0, -5, 201, "many", 10**7])
def test_a_quantity_that_is_a_slip_is_refused(qty):
    before = stock("amlodipine")
    with pytest.raises(pharmacy.Refused):
        pharmacy.dispense("abc", 7, "amlodipine", qty, allowed=10**9)
    assert stock("amlodipine") == before


def test_more_than_the_shelf_holds_is_refused():
    with pytest.raises(pharmacy.Refused):
        pharmacy.dispense("abc", 7, "insulin", 35, allowed=35)


def test_a_second_supply_on_one_ticket_needs_the_supervisor():
    pharmacy.dispense("abc", 7, "insulin", 1, allowed=1)
    before = stock("insulin")
    for pin, reason in ((None, None), ("0000", "lost"), (PIN, "")):
        with pytest.raises(pharmacy.NeedsSupervisor):
            pharmacy.dispense("abc", 7, "insulin", 1, pin, reason)
    assert stock("insulin") == before
    row = pharmacy.dispense("abc", 7, "insulin", 1, PIN, "First vial was broken")
    assert row["approved"] == "supervisor" and stock("insulin") == before - 1
    pharmacy.dispense("other", 8, "insulin", 1, allowed=1)         # another ticket with its own prescription


def test_a_stock_count_cannot_be_changed_without_the_supervisor():
    before = stock("paracetamol")
    for pin, reason in ((None, "stock take"), ("1111", "stock take"), (PIN, " ")):
        with pytest.raises(pharmacy.NeedsSupervisor):
            pharmacy.adjust("paracetamol", 10, pin, reason)
    assert stock("paracetamol") == before
    row = pharmacy.adjust("paracetamol", before + 500, PIN, "Delivery of 500")
    assert (row["was"], row["now"], row["qty"]) == (before, before + 500, 500)
    assert pharmacy.approvals(0)[0]["kind"] == "adjust"


def test_a_fee_waiver_needs_the_supervisor_and_a_reason():
    s = visits.new("sn")
    assert pharmacy.set_fee(s, "paid")["status"] == "paid"
    for pin, reason in ((None, "Pregnant"), ("9999", "Pregnant"), (PIN, None)):
        with pytest.raises(pharmacy.NeedsSupervisor):
            pharmacy.set_fee(s, "waived", pin, reason)
    assert s["fee"]["status"] == "paid"
    fee = pharmacy.set_fee(s, "waived", PIN, "Pregnant")
    assert fee["approved"] == "supervisor" and pharmacy.approvals(0)[0]["kind"] == "waiver"


def test_over_the_web_a_waiver_without_the_pin_answers_403_and_wrong_tries_are_limited():
    s = visits.new("sn")
    s["status"] = "ready"
    c = TestClient(server.app)
    assert c.post(f"/api/visits/{s['id']}/fee", json={"status": "waived", "reason": "Pregnant"}).status_code == 403
    assert c.post(f"/api/visits/{s['id']}/fee", json={"status": "waived", "reason": "Pregnant", "pin": PIN}).status_code == 200
    assert s["fee"]["status"] == "waived"
    for _ in range(10):
        r = c.post("/api/pharmacy/adjust", json={"med": "insulin", "counted": 999, "pin": "0000", "reason": "x"})
    assert r.status_code == 429 and stock("insulin") == 34


def test_a_photo_is_kept_beside_the_recordings_and_goes_with_the_visit():
    s = visits.new("sn")
    c = TestClient(server.app)
    jpeg = b"\xff\xd8\xff\xe0" + b"0" * 2000
    assert c.post(f"/api/visits/{s['id']}/photo", files={"file": ("p.jpg", b"not a picture", "image/jpeg")}).status_code == 400
    assert c.post(f"/api/visits/{s['id']}/photo", files={"file": ("p.jpg", jpeg + b"0" * 500_000, "image/jpeg")}).status_code == 400
    r = c.post(f"/api/visits/{s['id']}/photo", files={"file": ("p.jpg", jpeg, "image/jpeg")})
    assert r.status_code == 200 and r.json()["photo"]
    assert c.get(f"/api/visits/{s['id']}/photo").content == jpeg
    path = visits.photo_path(s)
    visits.remove(s["id"])
    assert not path.exists()


def test_the_photo_and_the_fee_never_reach_a_model_or_the_level():
    from app import prompts, triage
    s = visits.new("sn")
    before = triage.combine(visits._checks(s))
    pharmacy.set_fee(s, "waived", PIN, "Pregnant")
    assert triage.combine(visits._checks(s)) == before
    assert "photo" not in prompts.NOTE_SYSTEM.lower() and "fee" not in prompts.interview_system("sn").lower().split()


def test_the_doctor_types_the_diagnosis_and_the_prescription():
    s = visits.new("sn")
    for bad in (("", "treated", []), ("Malaria", "cured", []), ("Malaria", "treated", [{"med": "gold", "qty": 1}]),
                ("Malaria", "treated", [{"med": "ors", "qty": 0}]),
                ("Malaria", "treated", [{"med": "ors", "qty": 2}, {"med": "ors", "qty": 2}])):
        with pytest.raises(pharmacy.Refused):
            pharmacy.consult(s, *bad)
    assert "consult" not in s
    c = pharmacy.consult(s, "  High   blood pressure ", "treated", [{"med": "amlodipine", "qty": 30, "how": "1 a day"}])
    assert c["diagnosis"] == "High blood pressure" and c["rx"] == [{"med": "amlodipine", "qty": 30, "how": "1 a day"}]


def test_the_patient_moves_from_nurse_to_doctor_to_pharmacy_to_done():
    s = visits.new("sn")
    assert pharmacy.stage(s) == "intake"
    s["status"] = "ready"
    assert pharmacy.stage(s) == "nurse"
    s["status"] = "seen"
    assert pharmacy.stage(s) == "doctor"
    pharmacy.consult(s, "High blood pressure", "treated", [{"med": "amlodipine", "qty": 30}])
    assert pharmacy.stage(s) == "pharmacy" and pharmacy.remaining(s, "amlodipine") == 30
    pharmacy.dispense(s["id"], s["number"], "amlodipine", 30, allowed=pharmacy.remaining(s, "amlodipine"))
    assert pharmacy.stage(s) == "done" and pharmacy.remaining(s, "amlodipine") == 0
    s2 = visits.new("sn"); s2["status"] = "seen"
    pharmacy.consult(s2, "Headache", "treated", [])
    assert pharmacy.stage(s2) == "done"                       # nothing prescribed: no pharmacy step


def test_only_what_was_prescribed_leaves_the_shelf_without_the_supervisor():
    s = visits.new("sn"); s["status"] = "seen"
    pharmacy.consult(s, "High blood pressure", "treated", [{"med": "amlodipine", "qty": 30}])
    c = TestClient(server.app)
    give = lambda med, qty, **kw: c.post("/api/pharmacy/dispense", json={"sid": s["id"], "med": med, "qty": qty, **kw})
    assert give("insulin", 1).status_code == 403                  # not on the prescription
    assert give("amlodipine", 60).status_code == 403              # more than prescribed
    assert give("amlodipine", 30).status_code == 200
    assert give("amlodipine", 30).status_code == 403              # a second supply
    assert give("amlodipine", 30, pin=PIN, reason="First strip was damaged").status_code == 200
    assert [r["kind"] for r in pharmacy.approvals(0)] == ["dispense"]


def test_a_model_never_writes_the_diagnosis():
    from app import prompts
    assert "do not diagnose" in prompts.NOTE_SYSTEM.lower()
    s = visits.new("sn"); s["status"] = "ready"
    c = TestClient(server.app)
    assert c.post(f"/api/visits/{s['id']}/consult", json={"diagnosis": "", "outcome": "treated"}).status_code == 400
    r = c.post(f"/api/visits/{s['id']}/consult", json={"diagnosis": "Malaria", "outcome": "referred"})
    assert r.status_code == 200 and r.json()["consult"]["diagnosis"] == "Malaria" and s["status"] == "seen"
