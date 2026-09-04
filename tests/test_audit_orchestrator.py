import unittest
from unittest.mock import Mock, patch

from skills.audit_orchestrator import audit_site
from skills.audit_orchestrator.orchestrator import (
    engagement_stub,
    freshness_stub,
)
from skills.crawl_render_audit.scripts.models import PageResult
from skills.crawl_render_audit.scripts.crawler import WebsiteCrawler


class AuditOrchestratorTests(unittest.TestCase):

    def setUp(self):
        self.page = PageResult(
            url="https://example.com",
            depth=0,
            h1=["Example page"],
        )
        self.crawler = Mock()
        self.crawler.crawl.return_value = [self.page]

    def test_simple_url_includes_p2_findings(self):
        with patch.object(
            WebsiteCrawler,
            "crawl",
            return_value=[self.page],
        ) as crawl:
            findings = audit_site("https://example.com")

        crawl.assert_called_once_with("https://example.com")
        self.assertEqual(
            [finding["title"] for finding in findings],
            [
                "Missing meta description",
                "Missing JSON-LD structured data",
                "Missing canonical",
            ],
        )

    def test_empty_p3_stubs_leave_pipeline_clean(self):
        findings = audit_site(
            "https://example.com",
            crawler=self.crawler,
            freshness_provider=freshness_stub,
            engagement_provider=engagement_stub,
        )

        self.assertEqual(len(findings), 3)
        self.assertTrue(
            all(
                finding["source_skill"] == "crawl-render-audit"
                for finding in findings
            )
        )

    def test_invalid_provider_severity_is_rejected(self):
        invalid_finding = {
            "id": "F-INVALID",
            "source_skill": "freshness-corroboration",
            "url": "https://example.com",
            "category": "freshness",
            "title": "Invalid test finding",
            "severity": "urgent",
            "evidence": "Test evidence",
            "why_it_matters": "Test impact",
            "suggested_action": {
                "summary": "Test action",
                "priority": "urgent",
            },
        }

        with self.assertRaises(ValueError):
            audit_site(
                "https://example.com",
                crawler=self.crawler,
                freshness_provider=lambda url: [invalid_finding],
            )

    def test_findings_are_predictable_and_normalized(self):
        finding = {
            "id": "F-FRESHNESS-001",
            "source_skill": "freshness-corroboration",
            "url": "https://example.com",
            "category": "freshness",
            "title": "Test freshness finding",
            "severity": "MeDiUm",
            "evidence": "Test evidence",
            "why_it_matters": "Test impact",
            "suggested_action": {
                "summary": "Test action",
                "priority": "MeDiUm",
            },
        }

        findings = audit_site(
            "https://example.com",
            crawler=self.crawler,
            freshness_provider=lambda url: [finding],
        )

        self.assertEqual(
            [item["id"] for item in findings],
            [
                "F-META-DESC-327c3fda87",
                "F-JSON-LD-327c3fda87",
                "F-CANONICAL-327c3fda87",
                "F-FRESHNESS-001",
            ],
        )
        self.assertEqual(findings[-1]["severity"], "medium")
        self.assertEqual(
            findings[-1]["source_skill"],
            "freshness-corroboration",
        )

    def test_effective_page_url_is_preserved_in_findings(self):
        page = PageResult(
            url="https://example.com/start",
            final_url="https://example.com/effective",
            depth=0,
        )
        crawler = Mock()
        crawler.crawl.return_value = [page]

        findings = audit_site("https://example.com/start", crawler=crawler)

        self.assertTrue(findings)
        for finding in findings:
            self.assertEqual(finding["url"], page.final_url)
            self.assertIn(page.final_url, finding["evidence"])

    def test_deduplication_runs_after_provider_findings_are_collected(self):
        duplicate = {
            "id": "F-FRESHNESS-001",
            "source_skill": "freshness-corroboration",
            "url": "https://example.com",
            "category": "discoverability",
            "title": "Meta description is missing",
            "severity": "medium",
            "evidence": "Freshness provider evidence",
            "why_it_matters": "Test impact",
            "suggested_action": {
                "summary": "Test action",
                "priority": "medium",
            },
        }

        findings = audit_site(
            "https://example.com",
            crawler=self.crawler,
            freshness_provider=lambda url: [duplicate],
        )

        self.assertEqual(len(findings), 3)
        meta_finding = next(
            finding
            for finding in findings
            if finding["title"] == "Missing meta description"
        )
        self.assertIn("freshness-corroboration", meta_finding["evidence"])


if __name__ == "__main__":
    unittest.main()
