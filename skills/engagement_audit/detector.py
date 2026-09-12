import hashlib
import re
from typing import Any

from bs4 import BeautifulSoup

from shared.severity_policy import normalize_severity
from skills.crawl_render_audit.scripts.models import PageResult


SOURCE_SKILL = "engagement-audit"


def _page_url(page: PageResult) -> str:
    return page.final_url or page.url


def _finding_id(code: str, page_url: str) -> str:
    digest = hashlib.sha1(page_url.encode("utf-8")).hexdigest()[:10]
    return f"F-ENGAGEMENT-{code}-{digest}"


def _finding(page: PageResult, code: str, title: str, severity: str,
             evidence: str, why_it_matters: str, action: str) -> dict[str, Any]:
    normalized = normalize_severity(severity)
    return {
        "id": _finding_id(code, _page_url(page)),
        "source_skill": SOURCE_SKILL,
        "url": _page_url(page),
        "category": "engagement",
        "title": title,
        "severity": normalized,
        "evidence": evidence,
        "why_it_matters": why_it_matters,
        "suggested_action": {"summary": action, "priority": normalized},
    }


def _visible_text(page: PageResult) -> str:
    soup = BeautifulSoup(page.raw_html, "lxml")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def _page_kind(page: PageResult) -> str:
    path = page.url.lower().split("?", 1)[0]
    if path.rstrip("/").endswith(("/contact", "/contact-us")):
        return "contact"
    if any(token in path for token in ("/article", "/blog", "/news", "/resource")):
        return "article"
    if any(token in path for token in ("/product", "/service", "/solution", "/pricing")):
        return "decision"
    return "homepage" if page.depth == 0 else "general"


def _has_action(page: PageResult) -> bool:
    text = _visible_text(page).lower()
    return any(term in text for term in (
        "contact", "contact sales", "talk to sales", "get started",
        "learn more", "buy", "request", "demo", "try for free",
        "free trial", "start trial", "quote", "subscribe", "download",
        "sign up", "book", "apply",
    ))


def findings_for_page(page: PageResult) -> list[dict[str, Any]]:
    """Run context-aware engagement checks against one crawled page."""
    if not page.raw_html:
        return []

    text = _visible_text(page)
    if not text:
        return []

    findings: list[dict[str, Any]] = []
    kind = _page_kind(page)

    if kind == "homepage" and len(text.split()) < 20:
        findings.append(_finding(
            page, "ORIENTATION", "Homepage lacks enough orientation context", "high",
            f"Only {len(text.split())} visible words were extracted from {_page_url(page)}",
            "Direct visitors and AI-referred visitors may not understand the organization or its primary value.",
            "State who the organization serves, what it offers, and the primary next action in visible text.",
        ))

    if kind == "decision" and not _has_action(page):
        findings.append(_finding(
            page, "NEXT-ACTION", "Decision page lacks a clear next action", "high",
            f"No recognizable action language was found in visible text on {_page_url(page)}",
            "Visitors who arrive directly on a product or service page have no obvious path to continue evaluation or conversion.",
            "Add a context-appropriate CTA such as requesting a demo, contacting sales, starting a trial, or viewing pricing.",
        ))

    if kind == "contact" and not re.search(r"mailto:|tel:|<form\b|contact", page.raw_html, re.I):
        findings.append(_finding(
            page, "CONTACT-PATH", "Contact page lacks an actionable contact path", "high",
            f"No form, phone, email, or contact action was detected on {_page_url(page)}",
            "Visitors ready to ask a question or begin a relationship cannot identify how to reach the organization.",
            "Provide a usable form or clearly exposed email or phone contact path with an expected follow-up.",
        ))

    return findings


def engagement_stub(url: str) -> list[dict[str, Any]]:
    """Compatibility shim for callers that explicitly disable engagement."""
    return []