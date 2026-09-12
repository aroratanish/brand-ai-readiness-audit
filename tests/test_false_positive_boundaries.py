import unittest
from datetime import datetime, timezone

from skills.crawl_render_audit.scripts.models import PageResult
from skills.engagement_audit import findings_for_page as engagement_findings_for_page
from skills.freshness_corroboration import detect_freshness


AS_OF = datetime(2026, 9, 10, tzinfo=timezone.utc)


class FalsePositiveBoundaryTests(unittest.TestCase):

    def test_fp01_historical_report_date_is_not_stale(self):
        page = PageResult(
            url="https://example.com/reports/annual",
            depth=1,
            json_ld=[{"@type": "AnnualReport", "dateModified": "2020-01-01"}],
        )
        self.assertEqual(detect_freshness(page, as_of=AS_OF), [])

    def test_fp02_event_dates_are_not_freshness_dates(self):
        page = PageResult(
            url="https://example.com/event",
            depth=1,
            json_ld=[{"@type": "Event", "startDate": "2020-01-01", "endDate": "2020-01-02"}],
        )
        self.assertEqual(detect_freshness(page, as_of=AS_OF), [])

    def test_fp03_missing_date_is_not_stale(self):
        page = PageResult(
            url="https://example.com/article/guide",
            depth=1,
            json_ld=[{"@type": "Article", "headline": "Guide"}],
        )
        self.assertEqual(detect_freshness(page, as_of=AS_OF), [])

    def test_fp04_sales_ctas_are_valid_actions(self):
        page = PageResult(
            url="https://example.com/product/platform",
            depth=1,
            raw_html="<h1>Platform</h1><a href='/sales'>Talk to Sales</a>",
        )
        self.assertEqual(engagement_findings_for_page(page), [])

    def test_fp05_trial_demo_and_quote_ctas_are_valid_actions(self):
        for action in ("Try for free", "Start a free trial", "Request a quote"):
            page = PageResult(
                url="https://example.com/product/platform",
                depth=1,
                raw_html=f"<h1>Platform</h1><button>{action}</button>",
            )
            self.assertEqual(engagement_findings_for_page(page), [], action)

    def test_fp06_zero_internal_links_are_not_a_dead_end_finding(self):
        page = PageResult(
            url="https://example.com/confirmation",
            depth=1,
            raw_html="<h1>Payment complete</h1><p>Thank you.</p>",
            internal_links=[],
        )
        self.assertEqual(engagement_findings_for_page(page), [])


if __name__ == "__main__":
    unittest.main()