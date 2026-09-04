from datetime import datetime, timezone
from urllib.parse import urlparse

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


def build_report(url: str, findings: list[dict]) -> dict:
    """Build a canonical report from final deduplicated findings."""
    finding_list = list(findings)
    counts = {severity: 0 for severity in SEVERITY_KEYS}

    for finding in finding_list:
        severity = validate_finding_severity(finding)
        counts[severity] += 1

    return {
        "site": _site_name(url),
        "audited_at": _utc_timestamp(),
        "summary": {
            "total_findings": len(finding_list),
            **counts,
        },
        "findings": finding_list,
    }
