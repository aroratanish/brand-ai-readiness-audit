import hashlib
import re
from collections import defaultdict
from typing import Any

from bs4 import BeautifulSoup

from shared.severity_policy import normalize_severity
from skills.crawl_render_audit.scripts.models import PageResult

SOURCE_SKILL = "ai-discoverability-audit"
PRICE_RE = re.compile(r"(?<![\w])(?:₹|Rs\.?|INR|\$|USD|€|EUR|£|GBP)\s?\d[\d,]*(?:\.\d{1,2})?(?![\w])", re.I)
ACTION_WORDS = re.compile(r"\b(get started|start|buy|book|request|contact|demo|trial|subscribe|apply|quote|download)\b", re.I)


def _url(page):
    return page.final_url or page.url


def _id(code, value):
    return f"F-AI-{code}-{hashlib.sha1(value.encode()).hexdigest()[:10]}"


def _finding(page_url, code, title, severity, evidence, why, action, category="discoverability", confidence="high"):
    severity = normalize_severity(severity)
    return {
        "id": _id(code, page_url + title),
        "source_skill": SOURCE_SKILL,
        "url": page_url,
        "category": category,
        "title": title,
        "severity": severity,
        "confidence": confidence,
        "evidence": evidence,
        "why_it_matters": why,
        "suggested_action": {"summary": action, "priority": severity},
    }


def _visible_text(page):
    soup = BeautifulSoup(page.raw_html or "", "lxml")
    for element in soup(["script", "style", "noscript", "template"]):
        element.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def _iter_jsonld(value):
    if isinstance(value, list):
        for item in value:
            yield from _iter_jsonld(item)
    elif isinstance(value, dict):
        yield value
        if isinstance(value.get("@graph"), (list, dict)):
            yield from _iter_jsonld(value["@graph"])


def _types(obj):
    value = obj.get("@type") if isinstance(obj, dict) else None
    if isinstance(value, str):
        return {value.lower()}
    if isinstance(value, list):
        return {x.lower() for x in value if isinstance(x, str)}
    return set()


def _products(page):
    for obj in _iter_jsonld(page.json_ld):
        if "product" in _types(obj) and isinstance(obj, dict):
            yield obj


def _offers(product):
    offers = product.get("offers")
    if isinstance(offers, dict):
        offers = [offers]
    if isinstance(offers, list):
        for offer in offers:
            if isinstance(offer, dict):
                yield offer


def _first_price(product):
    for offer in _offers(product):
        price = offer.get("price")
        currency = offer.get("priceCurrency")
        if price is not None:
            return str(price), str(currency or "")
    return None


def findings_for_page(page: PageResult) -> list[dict[str, Any]]:
    if not page.raw_html:
        return []
    url = _url(page)
    text = _visible_text(page)
    findings = []

    for product in _products(page):
        name = product.get("name")
        price = _first_price(product)
        if name and price and text:
            visible_prices = PRICE_RE.findall(text)
            if not visible_prices:
                findings.append(_finding(
                    url, "PRODUCT-PRICE-VISIBLE", "Product price is only machine-marked, not visible in page text", "medium",
                    f"Product {name!r} has JSON-LD price {price[0]} {price[1]} but no currency/price pattern was found in visible text on {url}",
                    "A fact available only in structured data is less resilient to simple readers and can create inconsistent AI answers when visible content omits it.",
                    "Expose the current price and currency as visible, readable text near the product offer.",
                    confidence="medium",
                ))

    soup = BeautifulSoup(page.raw_html, "lxml")
    actionable = []
    for element in soup.find_all(["a", "button"]):
        label = " ".join(element.get_text(" ", strip=True).split())
        href = element.get("href", "")
        if ACTION_WORDS.search(label) and (element.name == "button" or href):
            actionable.append(label)
    if actionable and len(text.split()) < 35:
        findings.append(_finding(
            url, "ACTION-CONTEXT", "Action is present but lacks enough surrounding context", "medium",
            f"Found actionable control(s) {actionable[:3]!r}, while the page contains only {len(text.split())} visible words",
            "AI-referred visitors may reach an action without enough context to understand what they are agreeing to or what happens next.",
            "Add a concise value proposition and explain the action outcome, audience, and key prerequisite information next to the CTA.",
            category="engagement",
            confidence="medium",
        ))
    return findings


def _organization_names(page):
    names = []
    for obj in _iter_jsonld(page.json_ld):
        if _types(obj) & {"organization", "corporation", "brand"}:
            value = obj.get("name")
            if isinstance(value, str) and value.strip():
                names.append(value.strip())
    return names


def _normalize_name(value):
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _product_facts(page):
    facts = []
    for product in _products(page):
        name = product.get("name")
        price = _first_price(product)
        if isinstance(name, str) and name.strip() and price:
            facts.append((_normalize_name(name), name.strip(), price[0], price[1]))
    return facts


def findings_for_site(pages: list[PageResult]) -> list[dict[str, Any]]:
    findings = []
    orgs = defaultdict(list)
    products = defaultdict(list)
    for page in pages:
        url = _url(page)
        for name in _organization_names(page):
            orgs[_normalize_name(name)].append((url, name))
        for key, name, price, currency in _product_facts(page):
            products[key].append((url, name, price, currency))

    # Identity ambiguity: only report when two materially different org names occur.
    distinct_orgs = {}
    for _, entries in orgs.items():
        for url, name in entries:
            distinct_orgs.setdefault(_normalize_name(name), (url, name))
    if len(distinct_orgs) >= 2:
        items = list(distinct_orgs.values())
        materially_different = False
        for index, (_, first_name) in enumerate(items):
            for _, second_name in items[index + 1:]:
                from difflib import SequenceMatcher
                first_norm = _normalize_name(first_name)
                second_norm = _normalize_name(second_name)
                if (first_norm not in second_norm and second_norm not in first_norm
                        and SequenceMatcher(None, first_norm, second_norm).ratio() < 0.72):
                    materially_different = True
                    break
            if materially_different:
                break
        if materially_different:
            findings.append(_finding(
                items[0][0], "ORG-CONSISTENCY", "Organization identity differs across structured-data signals", "high",
                "; ".join(f"{name!r} on {url}" for url, name in items[:4]),
                "Conflicting first-party identity signals can cause AI systems to merge, split, or misattribute the brand entity.",
                "Choose one canonical organization name and use explicit Brand/Organization relationships or documented aliases where multiple brands are intentional.",
                category="entity-trust",
                confidence="high",
            ))

    # Cross-page product price conflict.
    for key, entries in products.items():
        normalized_prices = {(price, currency.upper()) for _, _, price, currency in entries}
        if len(normalized_prices) > 1:
            sample = "; ".join(f"{name!r}: {price} {currency} ({url})" for url, name, price, currency in entries[:5])
            findings.append(_finding(
                entries[0][0], "PRODUCT-PRICE-CONFLICT", "Conflicting structured product prices across pages", "high",
                sample,
                "AI systems can repeat an outdated or incorrect price when first-party pages disagree about a high-value commercial fact.",
                "Define a single source of truth for the current offer and synchronize visible content, structured data, and related product pages.",
                category="freshness",
                confidence="high",
            ))

    # Proactive opportunity: improve entity linking when Organization exists but has no sameAs.
    for page in pages:
        missing_same_as = False
        for obj in _iter_jsonld(page.json_ld):
            if _types(obj) & {"organization", "corporation"} and isinstance(obj, dict) and not obj.get("sameAs"):
                missing_same_as = True
                break
        if missing_same_as:
            findings.append(_finding(
                _url(page), "ORG-SAMEAS", "Opportunity: strengthen machine-readable entity linking", "low",
                f"Organization JSON-LD is present on {_url(page)} but has no sameAs property",
                "Explicit links to authoritative profiles can help machine readers distinguish the organization from similarly named entities.",
                "Where applicable, add accurate sameAs links to authoritative company profiles and keep them consistent with the visible brand.",
                category="opportunity",
                confidence="high",
            ))
            break
    return findings
