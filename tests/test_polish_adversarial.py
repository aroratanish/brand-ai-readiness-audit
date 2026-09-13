from skills.audit_orchestrator.polish import (
    build_evidence_graph, build_referral_journey, rank_actions,
    external_corroboration, organization_name,
)
from skills.crawl_render_audit.scripts.models import PageResult


def page(url, html, json_ld=None, depth=1):
    return PageResult(url=url, depth=depth, raw_html=html, title="Page", h1=["Page"], json_ld=json_ld or [], canonical=url)


def test_empty_site_journey_is_safe():
    assert build_referral_journey([])["overall"] == 0


def test_homepage_without_h1_reduces_discovery():
    p=page("https://x.test", "<title>X</title><p>Welcome</p>", depth=0)
    p.h1=[]
    assert build_referral_journey([p])["stages"]["discovery"] == 0


def test_decision_stage_uses_action_not_word_count_only():
    p=page("https://x.test/product/a", "<h1>A</h1><p>Useful product.</p><a href='/buy'>Buy</a>")
    assert build_referral_journey([p])["stages"]["decision"] == 100


def test_decision_stage_bottleneck_is_exposed():
    p=page("https://x.test/product/a", "<h1>A</h1><p>Useful product.</p>")
    result=build_referral_journey([p])
    assert result["bottleneck"] in result["stages"]


def test_graph_contains_page_and_product_nodes():
    p=page("https://x.test/product/a", "<h1>A</h1><p>$99</p>", [{"@type":"Product","name":"A","offers":{"price":"99","priceCurrency":"USD"}}])
    g=build_evidence_graph([p])
    kinds={n["kind"] for n in g["nodes"]}
    assert "page" in kinds and "product" in kinds and "price" in kinds


def test_graph_marks_conflicting_structured_prices():
    ld=lambda price:[{"@type":"Product","name":"A","offers":{"price":price,"priceCurrency":"USD"}}]
    g=build_evidence_graph([page("https://x.test/a","<p>A</p>",ld("99")),page("https://x.test/b","<p>A</p>",ld("109"))])
    assert g["conflict_edges"] >= 1


def test_graph_preserves_internal_link_edges():
    p=page("https://x.test/", '<a href="https://x.test/product">Product</a>', depth=0)
    p.internal_links=["https://x.test/product"]
    assert any(e["relation"]=="links_to" for e in build_evidence_graph([p])["edges"])


def test_rank_actions_prioritizes_high_confidence_high_severity():
    fs=[{"id":"a","severity":"high","confidence":"high","category":"discoverability","title":"A","evidence":"long evidence","suggested_action":{"summary":"Add clear context","priority":"high"}}, {"id":"b","severity":"low","confidence":"high","category":"engagement","title":"B","evidence":"long evidence","suggested_action":{"summary":"Review wording","priority":"low"}}]
    r=rank_actions(fs)
    assert r[0]["priority_rank"]==1 and r[0]["priority_score"]>r[1]["priority_score"]


def test_rank_actions_exposes_impact_and_effort():
    r=rank_actions([{"id":"a","severity":"medium","confidence":"medium","category":"freshness","title":"A","evidence":"evidence","suggested_action":{"summary":"Synchronize the current offer source","priority":"medium"}}])[0]
    assert 0 < r["impact_score"] <= 100 and 0 < r["effort_score"] <= 100 and "priority_score" in r


def test_organization_name_prefers_jsonld():
    p=page("https://x.test", "<title>Wrong</title>", [{"@type":"Organization","name":"Acme Labs"}], depth=0)
    assert organization_name([p])=="Acme Labs"


def test_external_corroboration_does_not_fetch_without_external_links(monkeypatch):
    p=page("https://x.test", "<h1>Acme Labs</h1>", [{"@type":"Organization","name":"Acme Labs"}], depth=0)
    called=[]
    monkeypatch.setattr("skills.audit_orchestrator.polish.requests.get", lambda *a,**k: called.append(a) or None)
    result=external_corroboration([p])
    assert result["status"]=="checked" and result["sources_checked"]==0 and not called


def test_external_corroboration_ignores_social_links(monkeypatch):
    p=page("https://x.test", "<h1>Acme Labs</h1>", [{"@type":"Organization","name":"Acme Labs"}], depth=0)
    p.external_links=["https://linkedin.com/company/acme","https://www.youtube.com/acme"]
    monkeypatch.setattr("skills.audit_orchestrator.polish.requests.get", lambda *a,**k: (_ for _ in ()).throw(AssertionError("social link should not be fetched")))
    result=external_corroboration([p])
    assert result["sources_checked"]==0
