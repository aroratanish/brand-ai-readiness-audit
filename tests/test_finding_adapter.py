import unittest

from skills.crawl_render_audit.scripts.finding_adapter import (
    findings_for_page,
)
from skills.crawl_render_audit.scripts.models import PageResult


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


class FindingAdapterTests(unittest.TestCase):

    def test_page_with_no_h1_produces_missing_h1_finding(self):
        findings = findings_for_page(
            PageResult(url="https://example.com/page", depth=0)
        )

        missing_h1 = next(
            finding for finding in findings
            if finding["title"] == "Missing H1 heading"
        )
        self.assertEqual(missing_h1["severity"], "medium")
        self.assertIn("https://example.com/page", missing_h1["evidence"])

    def test_one_h1_has_no_missing_or_multiple_h1_finding(self):
        findings = findings_for_page(
            PageResult(
                url="https://example.com/page",
                depth=0,
                h1=["Page heading"],
            )
        )

        titles = {finding["title"] for finding in findings}
        self.assertNotIn("Missing H1 heading", titles)
        self.assertNotIn("Multiple H1 headings", titles)

    def test_multiple_h1s_produce_multiple_h1_finding(self):
        findings = findings_for_page(
            PageResult(
                url="https://example.com/page",
                depth=0,
                h1=["First heading", "Second heading"],
            )
        )

        multiple_h1 = next(
            finding for finding in findings
            if finding["title"] == "Multiple H1 headings"
        )
        self.assertEqual(
            multiple_h1["evidence"],
            "Found 2 H1 headings on https://example.com/page",
        )

    def test_empty_h1_produces_empty_heading_finding(self):
        findings = findings_for_page(
            PageResult(
                url="https://example.com/page",
                depth=0,
                h1=["  "],
            )
        )

        empty_heading = next(
            finding for finding in findings
            if finding["title"] == "Empty heading text"
        )
        self.assertEqual(empty_heading["severity"], "low")
        self.assertIn("Empty H1 heading", empty_heading["evidence"])

    def test_empty_h2_produces_empty_heading_finding(self):
        findings = findings_for_page(
            PageResult(
                url="https://example.com/page",
                depth=0,
                h1=["Page heading"],
                h2=[""],
            )
        )

        empty_heading = next(
            finding for finding in findings
            if finding["title"] == "Empty heading text"
        )
        self.assertIn("Empty H2 heading", empty_heading["evidence"])

    def test_valid_json_ld_has_no_malformed_finding(self):
        findings = findings_for_page(
            PageResult(
                url="https://example.com/page",
                depth=0,
                json_ld=[{"@type": "WebPage"}],
            )
        )

        self.assertNotIn(
            "Malformed JSON-LD",
            {finding["title"] for finding in findings},
        )

    def test_malformed_json_ld_marker_produces_finding(self):
        findings = findings_for_page(
            PageResult(
                url="https://example.com/page",
                depth=0,
                json_ld=[{"_parse_error": True, "_raw": "{"}],
            )
        )

        malformed = next(
            finding for finding in findings
            if finding["title"] == "Malformed JSON-LD"
        )
        self.assertEqual(malformed["severity"], "medium")
        self.assertEqual(
            malformed["evidence"],
            "Malformed JSON-LD found on https://example.com/page",
        )

    def test_multiple_applicable_problems_produce_multiple_findings(self):
        page = PageResult(
            url="https://example.com/page",
            depth=0,
            h1=[],
            h2=["  "],
            json_ld=[{"_parse_error": True}],
        )

        findings = findings_for_page(page)
        titles = {finding["title"] for finding in findings}

        self.assertTrue({
            "Missing H1 heading",
            "Empty heading text",
            "Malformed JSON-LD",
        }.issubset(titles))

    def test_all_adapter_findings_have_canonical_fields(self):
        findings = findings_for_page(
            PageResult(
                url="https://example.com/page",
                depth=0,
                h1=["Heading", "Another heading"],
                h2=[""],
                json_ld=[{"_parse_error": True}],
            )
        )

        for finding in findings:
            self.assertTrue(REQUIRED_FINDING_FIELDS.issubset(finding))
            self.assertTrue({"summary", "priority"}.issubset(
                finding["suggested_action"]
            ))


if __name__ == "__main__":
    unittest.main()
