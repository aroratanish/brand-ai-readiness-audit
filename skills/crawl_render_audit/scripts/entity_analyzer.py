import re
from difflib import SequenceMatcher

from bs4 import BeautifulSoup


def _clean(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _entity_objects(json_ld: list[dict]) -> list[dict]:
    objects = []
    for item in json_ld or []:
        if not isinstance(item, dict):
            continue
        candidates = item.get("@graph", [item])
        if isinstance(candidates, dict):
            candidates = [candidates]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            types = candidate.get("@type", [])
            types = [types] if isinstance(types, str) else types
            if any(value in {"Organization", "Corporation", "Brand"} for value in types):
                objects.append(candidate)
    return objects


def analyze_entity(page) -> dict | None:
    """Return a finding only for a strong visible/schema identity mismatch."""
    organizations = _entity_objects(page.json_ld)
    if not organizations or not page.raw_html:
        return None

    schema_name = next((item.get("name") for item in organizations if item.get("name")), None)
    if not isinstance(schema_name, str) or not schema_name.strip():
        return None

    soup = BeautifulSoup(page.raw_html, "lxml")
    visible_candidates = []
    site_name = soup.find("meta", attrs={"property": "og:site_name"})
    if site_name and site_name.get("content"):
        visible_candidates.append(site_name["content"])
    for selector in ("header", "h1"):
        element = soup.find(selector)
        if element:
            text = element.get_text(" ", strip=True)
            if text:
                visible_candidates.append(text)

    visible_name = next((value for value in visible_candidates if _clean(value)), None)
    if not visible_name:
        return None

    similarity = SequenceMatcher(None, _clean(schema_name), _clean(visible_name)).ratio()
    if similarity >= 0.55:
        return None

    page_url = page.final_url or page.url
    return {
        "page_url": page_url,
        "schema_name": schema_name,
        "visible_name": visible_name,
        "confidence": "medium",
    }