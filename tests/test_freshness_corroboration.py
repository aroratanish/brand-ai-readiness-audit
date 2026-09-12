import unittest
from datetime import datetime, timezone

from skills.crawl_render_audit.scripts.models import PageResult
from skills.freshness_corroboration import detect_freshness


AS_OF = datetime(2026, 9, 10, tzinfo=timezone.utc)
REQUIRED_FINDING_FIELDS = {
    "id",
    "source_skill",
    "url",
    "category",
    "title",
    "severity",
    "evidence",
    "why_it_matters",
    "suggested_action",
}


class FreshnessCorroborationTests(unittest.TestCase):

    def test_old_date_modified_creates_finding(self):
        page = PageResult(
            url="https://example.com/article",
            depth=0,
            json_ld=[{"@type": "Article", "dateModified": "2024-01-01"}],
        )

        findings = detect_freshness(page, as_of=AS_OF)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["source_skill"], "freshness-corroboration")
        self.assertIn("dateModified", findings[0]["evidence"])

    def test_recent_date_modified_creates_no_finding(self):
        page = PageResult(
            url="https://example.com/article",
            depth=0,
            json_ld=[{"@type": "Article", "dateModified": "2026-08-01"}],
        )

        self.assertEqual(detect_freshness(page, as_of=AS_OF), [])

    def test_event_start_date_does_not_create_finding(self):
        page = PageResult(
            url="https://example.com/event",
            depth=0,
            json_ld=[
                {
                    "@type": "Event",
                    "startDate": "2020-01-01T09:00:00Z",
                    "endDate": "2020-01-01T17:00:00Z",
                }
            ],
        )

        self.assertEqual(detect_freshness(page, as_of=AS_OF), [])

    def test_missing_date_does_not_create_finding(self):
        page = PageResult(
            url="https://example.com/page",
            depth=0,
            json_ld=[{"@type": "WebPage"}],
        )

        self.assertEqual(detect_freshness(page, as_of=AS_OF), [])

    def test_finding_matches_shared_schema(self):
        page = PageResult(
            url="https://example.com/article",
            depth=0,
            json_ld=[{"datePublished": "2023-01-01"}],
        )

        finding = detect_freshness(page, as_of=AS_OF)[0]

        self.assertTrue(REQUIRED_FINDING_FIELDS.issubset(finding))
        self.assertEqual(finding["source_skill"], "freshness-corroboration")
        self.assertEqual(finding["category"], "freshness")
        self.assertEqual(
            {"summary", "priority"},
            set(finding["suggested_action"]),
        )


if __name__ == "__main__":
    unittest.main()