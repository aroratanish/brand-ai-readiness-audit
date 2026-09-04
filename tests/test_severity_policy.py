import unittest

from shared.severity_policy import (
    normalize_severity,
    validate_finding,
    validate_finding_severity,
)
from skills.crawl_render_audit.scripts.finding_adapter import (
    findings_for_page,
)
from skills.crawl_render_audit.scripts.models import PageResult


class SeverityPolicyTests(unittest.TestCase):

    def make_finding(self, severity="medium", evidence="Observed issue", priority=None):
        return {
            "severity": severity,
            "evidence": evidence,
            "suggested_action": {
                "summary": "Take action",
                "priority": priority if priority is not None else severity,
            },
        }

    def test_valid_severities(self):
        for severity in ("critical", "high", "medium", "low"):
            with self.subTest(severity=severity):
                self.assertEqual(normalize_severity(severity), severity)

    def test_mixed_case_is_normalized(self):
        self.assertEqual(normalize_severity("HiGh"), "high")

    def test_invalid_severity_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_severity("urgent")

    def test_missing_severity_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_finding_severity({})

    def test_valid_critical_requires_evidence(self):
        finding = self.make_finding("critical")

        self.assertIs(validate_finding(finding), finding)

    def test_critical_with_missing_evidence_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_finding(self.make_finding("critical", evidence=None))

    def test_critical_with_blank_evidence_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_finding(self.make_finding("critical", evidence="  "))

    def test_valid_severities_are_accepted(self):
        for severity in ("high", "medium", "low"):
            with self.subTest(severity=severity):
                self.assertEqual(
                    validate_finding(self.make_finding(severity))["severity"],
                    severity,
                )

    def test_invalid_finding_severity_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_finding(self.make_finding("urgent"))

    def test_missing_finding_severity_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_finding({"evidence": "Observed issue"})

    def test_finding_severity_and_priority_are_normalized(self):
        finding = self.make_finding("  HiGh  ", priority=" HIGH ")

        validate_finding(finding)

        self.assertEqual(finding["severity"], "high")
        self.assertEqual(finding["suggested_action"]["priority"], "high")

    def test_matching_priority_is_accepted(self):
        finding = self.make_finding("medium", priority="medium")

        self.assertIs(validate_finding(finding), finding)

    def test_mismatched_priority_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_finding(self.make_finding("high", priority="medium"))

    def test_explicitly_assigned_severity_is_preserved(self):
        finding = self.make_finding("low")

        validate_finding(finding)

        self.assertEqual(finding["severity"], "low")

    def test_policy_does_not_escalate_severity(self):
        finding = self.make_finding("low", evidence="Serious sounding text")

        validate_finding(finding)

        self.assertEqual(finding["severity"], "low")

    def test_adapter_findings_have_valid_severity(self):
        page = PageResult(url="https://example.com", depth=0)

        findings = findings_for_page(page)

        self.assertTrue(findings)
        for finding in findings:
            self.assertEqual(
                validate_finding_severity(finding),
                finding["severity"],
            )
            self.assertEqual(finding["url"], page.url)
            self.assertIn(page.url, finding["evidence"])


if __name__ == "__main__":
    unittest.main()
