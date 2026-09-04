import re
import unittest
from unittest.mock import Mock

from skills.audit_orchestrator import audit_site_report
from skills.audit_orchestrator.report_builder import build_report
from skills.crawl_render_audit.scripts.models import PageResult


def make_finding(finding_id, severity="medium"):
    return {
        "id": finding_id,
        "source_skill": "crawl-render-audit",
        "url": "https://example.com/page",
        "category": "discoverability",
        "title": "Test finding",
        "severity": severity,
        "evidence": "Test evidence",
        "why_it_matters": "Test impact",
        "suggested_action": {
            "summary": "Test action",
            "priority": severity,
        },
    }


class ReportBuilderTests(unittest.TestCase):

    def test_empty_findings_include_zero_counts(self):
        report = build_report("https://example.com/path", [])

        self.assertEqual(report["site"], "example.com")
        self.assertEqual(report["summary"], {
            "total_findings": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        })
        self.assertEqual(report["findings"], [])

    def test_one_finding_is_counted_and_preserved(self):
        findings = [make_finding("F-001", "high")]

        report = build_report("https://example.com", findings)

        self.assertEqual(report["summary"]["total_findings"], 1)
        self.assertEqual(report["summary"]["high"], 1)
        self.assertIs(report["findings"][0], findings[0])

    def test_multiple_severities_are_counted(self):
        findings = [
            make_finding("F-001", "critical"),
            make_finding("F-002", "critical"),
            make_finding("F-003", "high"),
            make_finding("F-004", "medium"),
            make_finding("F-005", "medium"),
            make_finding("F-006", "medium"),
        ]

        report = build_report("https://example.com", findings)

        self.assertEqual(report["summary"], {
            "total_findings": 6,
            "critical": 2,
            "high": 1,
            "medium": 3,
            "low": 0,
        })

    def test_audited_at_is_utc_iso8601(self):
        report = build_report("https://example.com", [])

        self.assertRegex(
            report["audited_at"],
            re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"),
        )

    def test_report_interface_preserves_orchestrator_findings(self):
        page = PageResult(
            url="https://example.com",
            depth=0,
            h1=["Example page"],
        )
        crawler = Mock()
        crawler.crawl.return_value = [page]

        report = audit_site_report("https://example.com", crawler=crawler)

        self.assertEqual(report["site"], "example.com")
        self.assertEqual(report["findings"][0]["url"], "https://example.com")
        self.assertEqual(report["summary"]["total_findings"], 3)


if __name__ == "__main__":
    unittest.main()
