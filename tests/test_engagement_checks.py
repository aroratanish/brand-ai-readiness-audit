from skills.engagement_audit import findings_for_page
from skills.engagement_audit.scripts.engagement_checks import run_checks
from skills.engagement_audit.scripts.engagement_adapter import build_engagement_evidence
from skills.crawl_render_audit.scripts.models import LinkResult, PageResult


def test_en01_requires_explicit_high_intent_context():
    assert "EN-01" not in {f["id"] for f in run_checks({"links": [], "buttons": [], "forms": []})}
    findings = run_checks({"high_intent": True, "links": [], "buttons": [], "forms": []})
    assert "EN-01" in {f["id"] for f in findings}


def test_en02_uses_observed_link_status_not_missing_status():
    page = {
        "high_intent": True,
        "links": [{
            "href": "/buy",
            "absolute_url": "https://example.com/buy",
            "text": "Buy now",
            "status_code": 404,
        }],
        "buttons": [],
        "forms": [],
    }
    assert "EN-02-1" in {f["id"] for f in run_checks(page)}


def test_en02_does_not_guess_when_status_is_unknown():
    page = {
        "high_intent": True,
        "links": [{"href": "/buy", "text": "Buy now"}],
        "buttons": [],
        "forms": [],
    }
    assert not any(f["id"].startswith("EN-02") for f in run_checks(page))


def test_empty_link_target_triggers_en02():
    page = {
        "high_intent": True,
        "links": [{"href": "", "absolute_url": "", "text": "Buy now"}],
        "buttons": [],
        "forms": [],
    }
    assert "EN-02-1" in {f["id"] for f in run_checks(page)}


def test_labelled_button_does_not_trigger_en03_or_en11():
    page = {
        "links": [],
        "buttons": [{"type": "button", "text": "Buy now"}],
        "forms": [],
    }
    ids = {f["id"] for f in run_checks(page)}
    assert not any(i.startswith("EN-03") for i in ids)
    assert not any(i.startswith("EN-11") for i in ids)


def test_unlabelled_button_triggers_en03():
    page = {"links": [], "buttons": [{"type": "button", "text": ""}], "forms": []}
    assert "EN-03-BUTTON-1" in {f["id"] for f in run_checks(page)}


def test_form_without_submit_triggers_en07():
    page = {
        "forms": [{
            "action": "/contact",
            "controls": [{"tag": "input", "type": "text", "name": "name"}],
            "has_submit": False,
        }],
        "links": [],
        "buttons": [],
    }
    assert "EN-07-1" in {f["id"] for f in run_checks(page)}


def test_form_with_submit_does_not_trigger_en07():
    page = {
        "forms": [{
            "action": "/contact",
            "controls": [{"tag": "input", "type": "submit", "value": "Submit"}],
            "has_submit": True,
        }],
        "links": [],
        "buttons": [],
    }
    assert "EN-07-1" not in {f["id"] for f in run_checks(page)}


def test_context_gated_checks_stay_unknown_without_explicit_evidence():
    page = {"links": [{"href": "/buy", "text": "Buy"}], "buttons": [], "forms": []}
    ids = {f["id"] for f in run_checks(page)}
    assert "EN-01" not in ids
    assert "EN-05" not in ids
    assert "EN-06" not in ids
    assert "EN-08" not in ids
    assert "EN-10" not in ids
    assert "EN-12" not in ids


def test_adapter_maps_page_type_and_link_result_status():
    page = PageResult(
        url="https://example.com/product/widget",
        depth=1,
        raw_html='<h1>Widget</h1><a href="/buy">Buy now</a>',
        technical_evidence={"page_type": {"primary_type": "product", "confidence": "high"}},
        link_results=[LinkResult(url="https://example.com/buy", status_code=404, success=False)],
    )
    evidence = build_engagement_evidence(page)
    assert evidence["page_type"]["primary_type"] == "product"
    assert evidence["links"][0]["status_code"] == 404


def test_runtime_engagement_is_conservative_for_articles_and_terminal_pages():
    article = PageResult(url="https://example.com/article/guide", depth=1, raw_html="<h1>Guide</h1><p>Useful information.</p>")
    terminal = PageResult(url="https://example.com/confirmation", depth=1, raw_html="<h1>Payment complete</h1><p>Thank you.</p>", internal_links=[])
    assert findings_for_page(article) == []
    assert findings_for_page(terminal) == []


def test_runtime_product_page_without_action_is_flagged():
    page = PageResult(
        url="https://example.com/product/widget",
        depth=1,
        raw_html="<h1>Widget</h1><p>Reliable product for teams.</p>",
        technical_evidence={"page_type": {"primary_type": "product", "confidence": "high"}},
    )
    titles = {f["title"] for f in findings_for_page(page)}
    assert "No actionable element was extracted" in titles


def test_runtime_form_without_submit_is_flagged():
    page = PageResult(url="https://example.com/contact", depth=1, raw_html="<h1>Contact</h1><form><input name='email'></form>")
    titles = {f["title"] for f in findings_for_page(page)}
    assert "Form has no extracted submit control" in titles

def test_en04_is_unknown_for_unclassified_page():
    page = {"title": "", "meta_description": "", "h1": [], "h2": []}
    assert "EN-04" not in {f["id"] for f in run_checks(page)}


def test_en04_flags_action_oriented_page_without_description():
    page = {
        "high_intent": True,
        "title": "",
        "meta_description": "",
        "h1": [],
        "h2": [],
    }
    assert "EN-04" in {f["id"] for f in run_checks(page)}


def test_adapter_extracts_direct_html_context_and_accessible_labels():
    page = PageResult(
        url="https://example.com/product/widget",
        depth=1,
        raw_html=(
            "<title>Widget</title>"
            "<meta name='description' content='A widget for teams'>"
            "<h1>Widget</h1><h2>Features</h2>"
            "<a href='/buy' aria-label='Buy widget'>Buy</a>"
            "<button title='Start trial'>Trial</button>"
        ),
    )
    evidence = build_engagement_evidence(page)
    assert evidence["title"] == "Widget"
    assert evidence["meta_description"] == "A widget for teams"
    assert evidence["h1"] == ["Widget"]
    assert evidence["h2"] == ["Features"]
    assert evidence["links"][0]["aria_label"] == "Buy widget"
    assert evidence["buttons"][0]["title"] == "Start trial"

