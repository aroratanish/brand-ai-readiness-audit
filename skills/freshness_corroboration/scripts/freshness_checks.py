"""Dependency-free deterministic freshness checks.

The crawler/orchestrator should adapt its real PageResult into the small logical
fields documented by SKILL.md. Functions return check-level findings; they do not
perform orchestration or deduplication.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any


def _text(value: Any) -> str:
    return str(value or "").strip()


def _parse_date(value: Any) -> date | None:
    text = _text(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None


def _finding(check_id: str, title: str, evidence: str, severity: str) -> dict[str, str]:
    return {"check_id": check_id, "title": title, "evidence": evidence, "severity": severity}


def check_update_date_presence(page: dict) -> dict | None:
    if not page.get("time_sensitive"):
        return None
    if any(_parse_date(page.get(k)) for k in ("published_at", "modified_at", "valid_through", "expiry_date")):
        return None
    return _finding("FR-01", "Time-sensitive content has no usable recency signal",
                    "The page is marked time-sensitive, but no publication, modification, or validity date was observed.", "medium")


def check_published_modified_consistency(page: dict) -> dict | None:
    published = _parse_date(page.get("published_at"))
    modified = _parse_date(page.get("modified_at"))
    if not published or not modified or modified >= published:
        return None
    return _finding("FR-02", "Modified date predates published date",
                    f"Published date is {published.isoformat()}, while modified date is {modified.isoformat()}.", "high")


def check_expiry(page: dict, today: date | None = None) -> dict | None:
    today = today or date.today()
    expiry = _parse_date(page.get("valid_through") or page.get("expiry_date"))
    if not expiry or expiry >= today or not page.get("presented_as_active"):
        return None
    return _finding("FR-03", "Expired offer or event is still presented as active",
                    f"Explicit validity date is {expiry.isoformat()}, before audit date {today.isoformat()}, while the item is marked active.", "high")


def _conflicts(items: Any) -> tuple[bool, str]:
    observations = []
    for item in items or []:
        if isinstance(item, dict) and item.get("value") is not None:
            observations.append((_text(item.get("url")), str(item.get("value"))))
    values = {v for _, v in observations}
    evidence = "; ".join(f"{url}: {value}" for url, value in observations)
    return len(values) > 1, evidence


def check_price_consistency(page: dict) -> dict | None:
    conflict, evidence = _conflicts(page.get("first_party_prices"))
    if not conflict:
        return None
    return _finding("FR-04", "Conflicting first-party prices", evidence, "high")


def check_availability_consistency(page: dict) -> dict | None:
    conflict, evidence = _conflicts(page.get("first_party_availability"))
    if not conflict:
        return None
    return _finding("FR-05", "Conflicting first-party availability", evidence, "high")


def check_sitemap_corroboration(page: dict) -> dict | None:
    sitemap = _parse_date(page.get("sitemap_lastmod"))
    observed = _parse_date(page.get("modified_at") or page.get("published_at"))
    if not sitemap or not observed or not page.get("sitemap_mismatch_supported"):
        return None
    if sitemap == observed:
        return None
    return _finding("FR-06", "Sitemap freshness signal conflicts with page evidence",
                    f"Sitemap lastmod is {sitemap.isoformat()}, while page freshness signal is {observed.isoformat()}, with supporting mismatch evidence recorded.", "medium")


def check_structured_visible_mismatch(page: dict) -> dict | None:
    structured = page.get("structured_value")
    visible = page.get("visible_value")
    if structured is None or visible is None or str(structured).strip() == str(visible).strip():
        return None
    return _finding("FR-07", "Structured data conflicts with visible content",
                    f"Structured value is '{structured}', while visible page value is '{visible}'.", "high")


def check_policy_freshness(page: dict, today: date | None = None) -> dict | None:
    if not page.get("policy"):
        return None
    today = today or date.today()
    effective = _parse_date(page.get("policy_effective_date"))
    current = _parse_date(page.get("policy_current_until"))
    if current and current < today:
        return _finding("FR-08", "Policy is presented beyond its stated validity",
                        f"Policy validity ended {current.isoformat()}, before audit date {today.isoformat()}.", "high")
    if effective and effective > today:
        return _finding("FR-08", "Future-effective policy is presented as current",
                        f"Policy effective date is {effective.isoformat()}, after audit date {today.isoformat()}, but page is marked current.", "high")
    return None


def check_cross_page_fact(page: dict) -> dict | None:
    conflict, evidence = _conflicts(page.get("first_party_facts"))
    if not conflict:
        return None
    return _finding("FR-09", "Conflicting first-party factual values", evidence, "high")


def check_time_sensitive_claim(page: dict) -> dict | None:
    claims = page.get("time_sensitive_claims") or []
    if not claims or page.get("currency_evidence"):
        return None
    claims_text = "; ".join(_text(c) for c in claims)
    return _finding("FR-10", "Time-sensitive claims lack sufficient currency evidence",
                    f"Observed time-sensitive claims: {claims_text}. No supporting currency evidence was provided.", "medium")


def run_checks(page: dict, today: date | None = None) -> list[dict]:
    checks = (
        lambda: check_update_date_presence(page),
        lambda: check_published_modified_consistency(page),
        lambda: check_expiry(page, today),
        lambda: check_price_consistency(page),
        lambda: check_availability_consistency(page),
        lambda: check_sitemap_corroboration(page),
        lambda: check_structured_visible_mismatch(page),
        lambda: check_policy_freshness(page, today),
        lambda: check_cross_page_fact(page),
        lambda: check_time_sensitive_claim(page),
    )
    return [result for check in checks if (result := check()) is not None]


if __name__ == "__main__":
    import json
    import sys
    payload = json.load(sys.stdin)
    print(json.dumps(run_checks(payload), indent=2))
