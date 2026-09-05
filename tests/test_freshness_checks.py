from datetime import date
from skills.freshness_corroboration.scripts.freshness_checks import run_checks

def test_expired_active_offer():
    page={"time_sensitive":True,"valid_through":"2026-01-01","presented_as_active":True}
    ids={x["check_id"] for x in run_checks(page, date(2026,9,4))}
    assert "FR-03" in ids

def test_structured_visible_mismatch():
    page={"structured_value":"₹100","visible_value":"₹120"}
    ids={x["check_id"] for x in run_checks(page, date(2026,9,4))}
    assert "FR-07" in ids
