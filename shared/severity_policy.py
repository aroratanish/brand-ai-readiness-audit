from collections.abc import Mapping
from collections.abc import MutableMapping


VALID_SEVERITIES = frozenset({
    "critical",
    "high",
    "medium",
    "low",
})


def normalize_severity(value: object) -> str:
    """Normalize and validate one severity value."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("severity is required")

    normalized = value.strip().lower()

    if normalized not in VALID_SEVERITIES:
        valid_values = ", ".join(sorted(VALID_SEVERITIES))
        raise ValueError(
            f"invalid severity {value!r}; expected one of: {valid_values}"
        )

    return normalized


def validate_finding_severity(finding: Mapping[str, object]) -> str:
    """Validate a finding's severity and return its normalized value."""
    return normalize_severity(finding.get("severity"))


def validate_finding(finding: MutableMapping[str, object]) -> MutableMapping[str, object]:
    """Normalize and validate a finding before it enters the pipeline."""
    severity = normalize_severity(finding.get("severity"))
    finding["severity"] = severity

    evidence = finding.get("evidence")
    if severity == "critical" and (
        not isinstance(evidence, str) or not evidence.strip()
    ):
        raise ValueError("critical findings require non-empty evidence")

    suggested_action = finding.get("suggested_action")
    if isinstance(suggested_action, MutableMapping) and "priority" in suggested_action:
        priority = normalize_severity(suggested_action["priority"])
        if priority != severity:
            raise ValueError(
                "suggested_action.priority must match finding severity"
            )
        suggested_action["priority"] = priority

    return finding
