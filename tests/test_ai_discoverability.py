import unittest

from skills.ai_discoverability_audit.detector import findings_for_page, findings_for_site
from skills.crawl_render_audit.scripts.models import PageResult


class AIDiscoverabilityTests(unittest.TestCase):
    def test_render_only_price_fact_is_flagged_when_visible_price_missing(self):
        page = PageResult(
            url="https://example.com/product/widget",
            depth=1,
            raw_html='<html><body><h1>Widget</h1><p>Great widget</p></body></html>',
            json_ld=[{"@type":"Product","name":"Widget","offers":{"price":"99","priceCurrency":"USD"}}],
        )
        findings = findings_for_page(page)
        self.assertTrue(any(f["id"].startswith("F-AI-PRODUCT-PRICE-VISIBLE") for f in findings))

    def test_cross_page_price_conflict(self):
        pages = [
            PageResult(url="https://example.com/a", depth=0, raw_html='<h1>Widget</h1>', json_ld=[{"@type":"Product","name":"Widget","offers":{"price":"99","priceCurrency":"USD"}}]),
            PageResult(url="https://example.com/b", depth=1, raw_html='<h1>Widget</h1>', json_ld=[{"@type":"Product","name":"Widget","offers":{"price":"109","priceCurrency":"USD"}}]),
        ]
        findings = findings_for_site(pages)
        self.assertTrue(any("Conflicting structured product prices" in f["title"] for f in findings))

    def test_similar_organization_aliases_are_not_false_positive(self):
        pages = [
            PageResult(url="https://example.com", depth=0, raw_html="<h1>Acme</h1>", json_ld=[{"@type": "Organization", "name": "Acme"}]),
            PageResult(url="https://example.com/about", depth=1, raw_html="<h1>Acme</h1>", json_ld=[{"@type": "Organization", "name": "Acme Inc."}]),
        ]
        findings = findings_for_site(pages)
        self.assertFalse(any(f["title"] == "Organization identity differs across structured-data signals" for f in findings))

    def test_organization_sameas_is_opportunity_not_defect(self):
        page = PageResult(url="https://example.com", depth=0, raw_html='<h1>Acme</h1>', json_ld=[{"@type":"Organization","name":"Acme"}])
        findings = findings_for_site([page])
        self.assertTrue(any(f["category"] == "opportunity" and "entity linking" in f["title"] for f in findings))


if __name__ == "__main__":
    unittest.main()
