from pathlib import Path
from skills.crawl_render_audit.scripts.html_parser import parse_html
from skills.crawl_render_audit.scripts.models import PageResult
from skills.crawl_render_audit.scripts.finding_adapter import findings_for_page
from skills.audit_orchestrator.enhanced_checks import render_semantic_findings, freshness_enhanced
from skills.engagement_audit import findings_for_page as engagement_findings

ROOT = Path(__file__).parent / "fixtures"

def page(name):
    html=(ROOT/name/"index.html").read_text()
    parsed=parse_html(html, "https://example.com/"+name)
    return PageResult(url="https://example.com/"+name, depth=0, raw_html=html,
        title=parsed["title"], meta_description=parsed["meta_description"], h1=parsed["h1"], h2=parsed["h2"],
        canonical=parsed["canonical"], internal_links=parsed["internal_links"], external_links=parsed["external_links"], json_ld=parsed["json_ld"])

def test_healthy_fixture_is_not_flagged_for_basic_missing_fields():
    p=page("healthy"); titles={f["title"] for f in findings_for_page(p)}
    assert "Missing meta description" not in titles
    assert "Missing canonical" not in titles
    assert "Missing H1 heading" not in titles

def test_commerce_fixture_has_action_context():
    p=page("commerce")
    assert "Decision page lacks a clear next action" not in {f["title"] for f in engagement_findings(p)}

def test_stale_fixture_is_detected():
    p=page("stale")
    assert any(f["category"] == "freshness" for f in freshness_enhanced(p))

def test_engagement_fixture_detects_empty_action_and_form():
    p=page("engagement")
    titles={f["title"] for f in engagement_findings(p)}
    assert "Form has no extracted submit control" in titles

def test_render_semantic_only_flags_important_content():
    p=page("js-heavy")
    p.rendered_html=p.raw_html.replace("<script>document.body.insertAdjacentHTML('beforeend','<p>Price $999. Buy the widget today.</p>')</script>", "<p>Price $999. Buy the widget today.</p>")
    p.technical_evidence={"raw_vs_rendered":{"status":"rendered_content_added","evidence":{"rendered_only_sample":"Price $999 Buy the widget today"}}}
    assert render_semantic_findings(p)
