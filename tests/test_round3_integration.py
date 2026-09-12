import json
import unittest
from pathlib import Path
from unittest.mock import Mock

from skills.audit_orchestrator import audit_site_report
from skills.crawl_render_audit.scripts.models import PageResult
from skills.engagement_audit import findings_for_page as engagement_findings_for_page
from skills.crawl_render_audit.scripts.finding_adapter import findings_for_page


ROOT = Path(__file__).parents[1]


class Round3IntegrationTests(unittest.TestCase):

    def test_engagement_checks_decision_page_without_overreporting_articles(self):
        product = PageResult(
            url="https://example.com/product/widget",
            depth=1,
            raw_html="<html><h1>Widget</h1><p>Reliable product for teams.</p></html>",
        )
        article = PageResult(
            url="https://example.com/article/guide",
            depth=1,
            raw_html="<html><h1>Guide</h1><p>Useful information.</p></html>",
        )

        product_titles = {item["title"] for item in engagement_findings_for_page(product)}
        article_titles = {item["title"] for item in engagement_findings_for_page(article)}

        self.assertIn("Decision page lacks a clear next action", product_titles)
        self.assertNotIn("Decision page lacks a clear next action", article_titles)

    def test_entity_mismatch_is_evidence_backed(self):
        page = PageResult(
            url="https://example.com/about",
            depth=1,
            raw_html=(
                '<meta property="og:site_name" content="Acme Labs">'
                "<h1>Acme Labs</h1>"
            ),
            json_ld=[{"@type": "Organization", "name": "Northstar Holdings"}],
        )

        entity_findings = [
            item for item in findings_for_page(page)
            if item["category"] == "entity-trust"
        ]

        self.assertEqual(len(entity_findings), 1)
        self.assertEqual(entity_findings[0]["confidence"], "medium")
        self.assertIn("Northstar Holdings", entity_findings[0]["evidence"])

    def test_report_composes_all_specialists_and_coverage(self):
        page = PageResult(
            url="https://example.com/product/widget",
            depth=0,
            raw_html="<html><h1>Widget</h1><p>Product information.</p></html>",
            json_ld=[{"@type": "Article", "dateModified": "2020-01-01"}],
        )
        crawler = Mock()
        crawler.crawl.return_value = {
            "pages": [page],
            "pages_discovered": 4,
            "robots": {"allowed": True},
            "sitemaps": {"checked": 1},
        }

        report = audit_site_report("https://example.com", crawler=crawler)
        sources = {item["source_skill"] for item in report["findings"]}

        self.assertIn("engagement-audit", sources)
        self.assertIn("freshness-corroboration", sources)
        self.assertEqual(report["summary"]["total_findings"], len(report["findings"]))
        self.assertIn("by_category", report["analysis"])
        self.assertIn("opportunities", report["analysis"])
        self.assertEqual(report["coverage"]["pages_discovered"], 4)

    def test_ai_discoverability_is_composed_into_report(self):
        page = PageResult(
            url="https://example.com/product/widget",
            depth=0,
            raw_html="<h1>Widget</h1><p>Great widget</p>",
            json_ld=[{"@type": "Product", "name": "Widget", "offers": {"price": "99", "priceCurrency": "USD"}}],
        )
        crawler = Mock()
        crawler.crawl.return_value = [page]
        report = audit_site_report("https://example.com", crawler=crawler)
        sources = {item["source_skill"] for item in report["findings"]}
        self.assertIn("ai-discoverability-audit", sources)

    def test_manifest_has_one_entrypoint_and_all_skill_paths(self):
        manifest = json.loads((ROOT / "marketplace.json").read_text())
        entrypoints = [item for item in manifest["skills"] if item.get("entrypoint")]

        self.assertEqual(len(entrypoints), 1)
        self.assertEqual(entrypoints[0]["id"], "audit-orchestrator")
        for item in manifest["skills"]:
            self.assertTrue((ROOT / item["path"]).is_dir())


if __name__ == "__main__":
    unittest.main()