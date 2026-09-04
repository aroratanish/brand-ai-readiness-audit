import unittest

from skills.audit_orchestrator.deduplication import deduplicate_findings


def make_finding(
    finding_id,
    url="https://example.com/page",
    category="discoverability",
    title="Missing meta description",
    severity="medium",
    source_skill="crawl-render-audit",
    evidence="Specific evidence",
):
    return {
        "id": finding_id,
        "source_skill": source_skill,
        "url": url,
        "category": category,
        "title": title,
        "severity": severity,
        "evidence": evidence,
        "why_it_matters": "Important impact",
        "suggested_action": {
            "summary": "Take action",
            "priority": severity,
        },
    }


class FindingDeduplicationTests(unittest.TestCase):

    def test_exact_duplicates_keep_first_canonical_finding(self):
        first = make_finding("F-001", evidence="Longer useful evidence")
        duplicate = make_finding("F-002", evidence="Short evidence")

        result = deduplicate_findings([first, duplicate])

        self.assertEqual(result, [first])

    def test_near_duplicate_titles_are_merged(self):
        first = make_finding("F-001")
        duplicate = make_finding(
            "F-002",
            title="Meta description is missing",
            evidence="More useful evidence",
        )

        result = deduplicate_findings([first, duplicate])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "F-001")
        self.assertEqual(result[0]["evidence"], "More useful evidence")

    def test_different_titles_same_url_and_category_remain_separate(self):
        result = deduplicate_findings([
            make_finding("F-001", title="Missing meta description"),
            make_finding("F-002", title="Missing canonical"),
        ])

        self.assertEqual([finding["id"] for finding in result], ["F-001", "F-002"])

    def test_same_title_and_category_different_urls_remain_separate(self):
        result = deduplicate_findings([
            make_finding("F-001", url="https://example.com/one"),
            make_finding("F-002", url="https://example.com/two"),
        ])

        self.assertEqual(len(result), 2)

    def test_same_url_different_categories_remain_separate(self):
        result = deduplicate_findings([
            make_finding("F-001", category="discoverability"),
            make_finding("F-002", category="structured-data"),
        ])

        self.assertEqual(len(result), 2)

    def test_cross_source_duplicate_preserves_producer_information(self):
        first = make_finding("F-001")
        duplicate = make_finding(
            "F-002",
            source_skill="freshness-corroboration",
            title="Meta description is missing",
        )

        result = deduplicate_findings([first, duplicate])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source_skill"], "crawl-render-audit")
        self.assertIn("freshness-corroboration", result[0]["evidence"])

    def test_output_order_is_deterministic(self):
        findings = [
            make_finding("F-002", title="Missing canonical"),
            make_finding("F-001"),
            make_finding("F-003", title="Meta description is missing"),
        ]

        first_result = deduplicate_findings(findings)
        second_result = deduplicate_findings(findings)

        self.assertEqual(first_result, second_result)
        self.assertEqual(
            [finding["id"] for finding in first_result],
            ["F-002", "F-001"],
        )


if __name__ == "__main__":
    unittest.main()
