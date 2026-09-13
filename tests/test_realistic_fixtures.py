import unittest

from skills.crawl_render_audit.scripts.finding_adapter import findings_for_page
from skills.crawl_render_audit.scripts.models import PageResult
from skills.engagement_audit import findings_for_page as engagement_findings
from skills.freshness_corroboration import findings_for_page as freshness_findings


class RealisticFixtureTests(unittest.TestCase):

    def test_product_trial_page_has_no_missing_action_finding(self):
        page = PageResult(
            url="https://fixture.test/product/platform",
            depth=1,
            raw_html="<h1>Platform</h1><p>Tools for teams.</p><a href='/trial'>Try for free</a>",
        )
        titles = {item["title"] for item in engagement_findings(page)}
        self.assertNotIn("Decision page lacks a clear next action", titles)

    def test_enterprise_sales_page_has_no_missing_action_finding(self):
        page = PageResult(
            url="https://fixture.test/solutions/enterprise",
            depth=1,
            raw_html="<h1>Enterprise</h1><a href='/sales'>Contact Sales</a>",
        )
        self.assertEqual(engagement_findings(page), [])

    def test_article_without_date_is_not_stale(self):
        page = PageResult(
            url="https://fixture.test/blog/guide",
            depth=1,
            raw_html="<h1>Guide</h1><p>Evergreen information.</p>",
        )
        self.assertEqual(freshness_findings(page), [])

    def test_stale_article_date_is_reported(self):
        page = PageResult(
            url="https://fixture.test/blog/old",
            depth=1,
            json_ld=[{"@type": "Article", "dateModified": "2020-01-01"}],
        )
        self.assertEqual(len(freshness_findings(page)), 1)

    def test_malformed_json_ld_is_reported(self):
        page = PageResult(
            url="https://fixture.test/product/broken-data",
            depth=1,
            json_ld=[{"_parse_error": True, "_raw": "{bad"}],
        )
        titles = {item["title"] for item in findings_for_page(page)}
        self.assertIn("Malformed JSON-LD", titles)

    def test_contact_and_terminal_pages_do_not_get_unsupported_cta_findings(self):
        contact = PageResult(
            url="https://fixture.test/contact",
            depth=1,
            raw_html="<h1>Contact</h1><form><input><button type='submit'>Send</button></form>",
        )
        terminal = PageResult(
            url="https://fixture.test/confirmation",
            depth=1,
            raw_html="<h1>Success</h1><p>Payment complete.</p>",
        )
        self.assertEqual(engagement_findings(contact), [])
        self.assertEqual(engagement_findings(terminal), [])


if __name__ == "__main__":
    unittest.main()