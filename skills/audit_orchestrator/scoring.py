from __future__ import annotations
from collections import Counter

SEVERITY_PENALTY = {"critical": 24, "high": 12, "medium": 6, "low": 2}
CATEGORY_WEIGHTS = {
    "discoverability": 1.0, "structured-data": .9, "crawlability": 1.0,
    "freshness": 1.0, "entity-trust": 1.1, "engagement": 1.0,
    "opportunity": .15,
}

def build_score(findings: list[dict], pages_audited: int) -> dict:
    score = 100.0
    for f in findings:
        cat = f.get("category", "discoverability")
        score -= SEVERITY_PENALTY.get(f.get("severity", "low"), 2) * CATEGORY_WEIGHTS.get(cat, 1.0)
    score = max(0.0, min(100.0, round(score, 1)))
    counts = Counter(f.get("category", "uncategorized") for f in findings if f.get("category") != "opportunity")
    def dim(categories):
        subset=[f for f in findings if f.get("category") in categories]
        value=100.0
        for f in subset: value -= SEVERITY_PENALTY.get(f.get("severity", "low"),2)*CATEGORY_WEIGHTS.get(f.get("category"),1.0)
        return max(0.0, round(value,1))
    return {
        "overall": score,
        "dimensions": {
            "discoverability": dim({"discoverability","structured-data","crawlability"}),
            "freshness": dim({"freshness"}),
            "entity_trust": dim({"entity-trust"}),
            "engagement": dim({"engagement"}),
        },
        "method": "Transparent severity-weighted heuristic; opportunities have minimal score impact.",
        "pages_audited": pages_audited,
        "finding_counts_by_category": dict(sorted(counts.items())),
    }
