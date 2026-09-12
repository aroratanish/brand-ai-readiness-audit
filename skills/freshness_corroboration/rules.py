from datetime import date, datetime, timezone
from typing import Any


FRESHNESS_MAX_AGE_DAYS = 365
FRESHNESS_FIELDS = ("dateModified", "datePublished")
REPORT_TYPES = frozenset({
    "AnnualReport",
    "FinancialReport",
    "Report",
})


def iter_json_ld_objects(value: Any):
    """Yield JSON-LD objects, including objects nested in @graph or lists."""
    if isinstance(value, list):
        for item in value:
            yield from iter_json_ld_objects(item)
    elif isinstance(value, dict):
        yield value
        if "@graph" in value:
            yield from iter_json_ld_objects(value["@graph"])


def _types(item: dict[str, Any]) -> set[str]:
    value = item.get("@type")
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return {item_type for item_type in value if isinstance(item_type, str)}
    return set()


def is_report_like(item: dict[str, Any]) -> bool:
    return bool(_types(item) & REPORT_TYPES)


def parse_freshness_date(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None

    text = value.strip()
    if not text or len(text) < 10:
        return None

    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed_date = date.fromisoformat(text[:10])
        except ValueError:
            return None
        parsed = datetime.combine(parsed_date, datetime.min.time())

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def is_stale(parsed_date: datetime, as_of: datetime) -> bool:
    current_time = as_of
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    else:
        current_time = current_time.astimezone(timezone.utc)

    return (current_time - parsed_date).days > FRESHNESS_MAX_AGE_DAYS