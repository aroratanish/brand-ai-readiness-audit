import unittest

from shared.report_formatter import format_report


class ReportFormatterTests(unittest.TestCase):

    def test_formatter_uses_score_counts_and_issue_details(self):
        report = {
            "site": "example.com",
            "audited_at": "2026-09-13T00:00:00Z",
            "score": {"overall": 88, "dimensions": {"engagement": 88}},
            "summary": {"critical": 0, "high": 1, "medium": 0, "low": 0},
            "findings": [{
                "id": "F-1",
                "title": "Missing action",
                "severity": "high",
                "url": "https://example.com/product",
                "evidence": "No CTA extracted",
                "why_it_matters": "Visitors cannot continue.",
                "suggested_action": {"summary": "Add a relevant CTA"},
            }],
        }

        text = format_report(report)

        self.assertIn("BRAND AI READINESS AUDIT", text)
        self.assertIn("Overall score: 88/100", text)
        self.assertIn("High: 1", text)
        self.assertIn("No CTA extracted", text)
        self.assertIn("Add a relevant CTA", text)

    def test_formatter_handles_empty_report(self):
        text = format_report({
            "site": "example.com",
            "audited_at": "2026-09-13T00:00:00Z",
            "score": {"overall": 100, "dimensions": {}},
            "summary": {},
            "findings": [],
        })
        self.assertIn("Overall score: 100/100", text)
        self.assertIn("- None", text)


if __name__ == "__main__":
    unittest.main()