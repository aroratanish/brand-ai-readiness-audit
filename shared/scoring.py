from collections.abc import Iterable, Mapping

from .severity_policy import normalize_severity


SEVERITY_PENALTIES = {
    "critical": 25,
    "high": 12,
    "medium": 5,
    "low": 2,
}

DIMENSIONS = (
    "discoverability",
    "freshness",
    "engagement",
    "trust",
)

CATEGORY_DIMENSIONS = {
    "discoverability": "discoverability",
    "structured-data": "discoverability",
    "crawl-render-audit": "discoverability",
    "freshness": "freshness",
    "engagement": "engagement",
    "entity-trust": "trust",
    "trust": "trust",
}


def _bounded_score(penalty: int) -> int:
    return max(0, min(100, 100 - penalty))


def score_findings(findings: Iterable[Mapping[str, object]]) -> dict:
    """Return deterministic overall and implemented-dimension scores."""
    overall_penalty = 0
    dimension_penalties = {dimension: 0 for dimension in DIMENSIONS}

    for finding in findings:
        severity = normalize_severity(finding.get("severity"))
        penalty = SEVERITY_PENALTIES[severity]
        overall_penalty += penalty

        dimension = CATEGORY_DIMENSIONS.get(finding.get("category"))
        if dimension is not None:
            dimension_penalties[dimension] += penalty

    return {
        "overall": _bounded_score(overall_penalty),
        "dimensions": {
            dimension: _bounded_score(penalty)
            for dimension, penalty in dimension_penalties.items()
        },
    }