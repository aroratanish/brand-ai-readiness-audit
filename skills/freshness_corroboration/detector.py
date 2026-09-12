import hashlib
from datetime import datetime, timezone
from typing import Any

from shared.severity_policy import normalize_severity
from skills.crawl_render_audit.scripts.models import PageResult

from .rules import FRESHNESS_FIELDS, is_report_like, is_stale
from .rules import iter_json_ld_objects, parse_freshness_date


SOURCE_SKILL = "freshness-corroboration"


def _finding_id(page_url: str, field: str) -> str:
    url_digest = hashlib.sha1(page_url.encode("utf-8")).hexdigest()[:10]
    return f"F-FRESHNESS-{field.upper()}-{url_digest}"


def _build_finding(page_url: str, field: str, date_value: str) -> dict[str, Any]:
    severity = normalize_severity("medium")
    return {
        "id": _finding_id(page_url, field),
        "source_skill": SOURCE_SKILL,
        "url": page_url,
        "category": "freshness",
        "title": "Stale JSON-LD freshness signal",
        "severity": severity,
        "evidence": (
            f"JSON-LD {field} value {date_value!r} is older than the freshness "
            f"threshold on {page_url}"
        ),
        "why_it_matters": (
            "An old publication or modification signal can reduce confidence "
            "that the page reflects current information."
        ),
        "suggested_action": {
            "summary": "Review the page content and update its JSON-LD freshness signal.",
            "priority": severity,
        },
    }


def _freshness_signal(page: PageResult) -> tuple[str, str, datetime] | None:
    for item in iter_json_ld_objects(page.json_ld):
        if is_report_like(item):
            continue

        for field in FRESHNESS_FIELDS:
            parsed_date = parse_freshness_date(item.get(field))
            if parsed_date is not None:
                return field, str(item[field]), parsed_date

    return None


def detect_freshness(
    page: PageResult,
    as_of: datetime | None = None,
) -> list[dict[str, Any]]:
    """Return supported freshness findings for one PageResult."""
    page_url = page.final_url or page.url
    signal = _freshness_signal(page)
    if signal is None:
        return []

    field, date_value, parsed_date = signal
    current_time = as_of or datetime.now(timezone.utc)
    if not is_stale(parsed_date, current_time):
        return []

    return [_build_finding(page_url, field, date_value)]


def findings_for_page(
    page: PageResult,
    as_of: datetime | None = None,
) -> list[dict[str, Any]]:
    """Compatibility alias for the repository's page-finding convention."""
    return detect_freshness(page, as_of=as_of)