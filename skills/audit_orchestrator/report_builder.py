from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlparse

from shared.scoring import score_findings
from shared.severity_policy import validate_finding_severity


SEVERITY_KEYS = ("critical", "high", "medium", "low")


def _site_name(url: str) -> str:
    parsed = urlparse(url)
    return (parsed.hostname or parsed.netloc or url).lower()


def _utc_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def build_report(url: str, findings: list[dict], coverage: dict | None = None) -> dict:
    """Build a canonical report from final deduplicated findings."""
    finding_list = list(findings)
    counts = {severity: 0 for severity in SEVERITY_KEYS}

    for finding in finding_list:
        severity = validate_finding_severity(finding)
        counts[severity] += 1

    category_counts = Counter(finding.get("category", "uncategorized") for finding in finding_list)
    opportunity_count = sum(1 for finding in finding_list if finding.get("category") == "opportunity")
    confidence_counts = Counter(finding.get("confidence", "unknown") for finding in finding_list)
    evidence_strength_counts = Counter(finding.get("evidence_strength", "unknown") for finding in finding_list)

    report = {
        "site": _site_name(url),
        "audited_at": _utc_timestamp(),
        "summary": {
            "total_findings": len(finding_list),
            **counts,
        },
        "analysis": {
            "opportunities": opportunity_count,
            "by_category": dict(sorted(category_counts.items())),
            "by_confidence": dict(sorted(confidence_counts.items())),
            "by_evidence_strength": dict(sorted(evidence_strength_counts.items())),
        },
        "score": score_findings(finding_list),
        "findings": finding_list,
    }
    if coverage:
        report["coverage"] = coverage
    return report
