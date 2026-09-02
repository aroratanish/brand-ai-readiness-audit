import json
from bs4 import BeautifulSoup

from .url_utils import make_absolute_url, get_domain


def parse_html(html: str, page_url: str):
    soup = BeautifulSoup(html, "lxml")

    result = {
        "title": None,
        "meta_description": None,
        "h1": [],
        "h2": [],
        "canonical": None,
        "internal_links": [],
        "external_links": [],
        "json_ld": [],
    }

    # Title
    title = soup.find("title")

    if title:
        result["title"] = title.get_text(" ", strip=True)

    # Meta description
    description = soup.find(
        "meta",
        attrs={"name": lambda value: value and value.lower() == "description"},
    )

    if description:
        result["meta_description"] = description.get("content")

    # Headings
    result["h1"] = [
        heading.get_text(" ", strip=True)
        for heading in soup.find_all("h1")
    ]

    result["h2"] = [
        heading.get_text(" ", strip=True)
        for heading in soup.find_all("h2")
    ]

    # Canonical
    canonical = soup.find(
        "link",
        attrs={"rel": lambda value: value and "canonical" in value},
    )

    if canonical:
        href = canonical.get("href")

        if href:
            result["canonical"] = make_absolute_url(page_url, href)

    # Links
    base_domain = get_domain(page_url)

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href")

        if not href:
            continue

        if href.startswith(("mailto:", "tel:", "javascript:")):
            continue

        absolute_url = make_absolute_url(page_url, href)

        if get_domain(absolute_url) == base_domain:
            result["internal_links"].append(absolute_url)
        else:
            result["external_links"].append(absolute_url)

    # JSON-LD
    for script in soup.find_all(
        "script",
        attrs={"type": "application/ld+json"},
    ):
        raw = script.string or script.get_text()

        if not raw.strip():
            continue

        try:
            data = json.loads(raw)
            result["json_ld"].append(data)

        except json.JSONDecodeError:
            result["json_ld"].append(
                {
                    "_parse_error": True,
                    "_raw": raw[:1000],
                }
            )

    # Remove duplicate links
    result["internal_links"] = list(
        dict.fromkeys(result["internal_links"])
    )

    result["external_links"] = list(
        dict.fromkeys(result["external_links"])
    )

    return result