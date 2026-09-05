from skills.engagement_audit.scripts.engagement_checks import run_checks

def test_missing_high_intent_cta():
    page={"high_intent":True,"intent":"purchase","ctas":[]}
    ids={x["check_id"] for x in run_checks(page)}
    assert "EN-01" in ids

def test_broken_core_cta():
    page={"url":"https://example.com/","ctas":[{"text":"Buy","target":"/buy","status":404}]}
    ids={x["check_id"] for x in run_checks(page)}
    assert "EN-02" in ids
