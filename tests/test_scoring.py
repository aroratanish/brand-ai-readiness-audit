import unittest

from shared.scoring import score_findings


def finding(category, severity, finding_id="F-1"):
    return {"id": finding_id, "category": category, "severity": severity}


class ScoringTests(unittest.TestCase):

    def test_zero_findings_have_perfect_scores(self):
        result = score_findings([])
        self.assertEqual(result["overall"], 100)
        self.assertEqual(set(result["dimensions"]), {
            "discoverability", "freshness", "engagement", "trust",
        })
        self.assertTrue(all(value == 100 for value in result["dimensions"].values()))

    def test_severity_penalties_are_explainable_and_bounded(self):
        result = score_findings([
            finding("discoverability", "high"),
            finding("engagement", "medium", "F-2"),
            finding("freshness", "low", "F-3"),
        ])
        self.assertEqual(result["overall"], 81)
        self.assertEqual(result["dimensions"]["discoverability"], 88)
        self.assertEqual(result["dimensions"]["engagement"], 95)
        self.assertEqual(result["dimensions"]["freshness"], 98)
        self.assertEqual(result["dimensions"]["trust"], 100)

    def test_unknown_category_affects_overall_not_invented_dimension(self):
        result = score_findings([finding("future-category", "critical")])
        self.assertEqual(result["overall"], 75)
        self.assertTrue(all(value == 100 for value in result["dimensions"].values()))

    def test_repeated_input_is_deterministic(self):
        findings = [finding("entity-trust", "medium")]
        self.assertEqual(score_findings(findings), score_findings(findings))


if __name__ == "__main__":
    unittest.main()