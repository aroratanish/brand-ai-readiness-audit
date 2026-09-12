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


def _action_elements(page: PageResult) -> list[str]:
    """Return labels for genuinely actionable links/buttons, not prose mentions."""
    soup = BeautifulSoup(page.raw_html or "", "lxml")
    labels = []
    for element in soup.find_all(["a", "button", "input"]):
        label = " ".join(element.get_text(" ", strip=True).split())
        if element.name == "input":
            label = " ".join(filter(None, [element.get("value", ""), element.get("aria-label", "")]))
        href = element.get("href")
        input_type = (element.get("type") or "").lower()
        actionable_target = element.name == "button" or element.name == "input" or bool(href)
        is_submit = element.name == "input" and input_type in {"submit", "button", "image"}
        if actionable_target and (ACTION_TERMS.search(label) or is_submit):
            labels.append(label or element.name)
    return list(dict.fromkeys(labels))


ACTION_TERMS = re.compile(
    r"\b(contact|contact sales|talk to sales|get started|start|learn more|buy|request|demo|try|free trial|start trial|quote|subscribe|download|sign up|book|apply)\b",
    re.I,
)

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

    action_elements = _action_elements(page)

    if kind == "decision" and not action_elements:
        findings.append(_finding(
            page, "NEXT-ACTION", "Decision page lacks a clear next action", "high",
            f"No recognizable action language was found in visible text on {_page_url(page)}",
            "Visitors who arrive directly on a product or service page have no obvious path to continue evaluation or conversion.",
            "Add a context-appropriate CTA such as requesting a demo, contacting sales, starting a trial, or viewing pricing.",
        ))

    if kind == "contact" and not re.search(r"mailto:|tel:|<form\b", page.raw_html, re.I) and not re.search(r"\b(email|phone|call|contact)\b", text, re.I):
        findings.append(_finding(
            page, "CONTACT-PATH", "Contact page lacks an actionable contact path", "high",
            f"No form, phone, email, or contact action was detected on {_page_url(page)}",
            "Visitors ready to ask a question or begin a relationship cannot identify how to reach the organization.",
            "Provide a usable form or clearly exposed email or phone contact path with an expected follow-up.",
        ))

    soup = BeautifulSoup(page.raw_html, "lxml")
    forms = soup.find_all("form")
    for form in forms:
        submit = form.find(["button", "input"], attrs={"type": lambda value: value and value.lower() in {"submit", "button"}})
        if submit is None and not form.find("button"):
            findings.append(_finding(
                page, "FORM-ACTION", "Form lacks a clear submit control", "medium",
                f"A form is present on {_page_url(page)} but no submit/button control was found in that form",
                "A visitor can reach an apparent conversion path but may not have a clear way to complete the requested action.",
                "Add a clearly labeled submit control and explain what happens after submission.",
            ))

    # Empty actionable controls are a stronger engagement defect than generic
    # absence of a CTA and can be established directly from the HTML.
    for element in soup.find_all(["a", "button"]):
        label = " ".join(element.get_text(" ", strip=True).split())
        label = label or element.get("aria-label", "") or element.get("title", "")
        href = element.get("href")
        if element.name == "a" and href in ("", "#", "#!") and (ACTION_TERMS.search(label) or element.get("role") == "button"):
            findings.append(_finding(
                page, "EMPTY-ACTION", "Action control has no usable destination", "high",
                f"Action '{label or '(unlabelled)'}' uses an empty or fragment-only href on {_page_url(page)}.",
                "A visitor may be presented with a conversion action that has no directly addressable destination.",
                "Provide a real destination or implement the control as a clearly defined interaction with an accessible state and outcome.",
            ))

    # Contact pages should expose a concrete route, not just the word
    # 'contact'. This complements the existing broad contact-path check.
    if kind == "contact":
        concrete = bool(soup.find("form")) or bool(soup.find(href=re.compile(r"^(mailto:|tel:)", re.I)))
        if not concrete and not re.search(r"\b(?:email|phone|call)\b", text, re.I):
            findings.append(_finding(
                page, "CONTACT-CONCRETE", "Contact page lacks a concrete contact mechanism", "medium",
                f"No form, mailto/tel link, email, or phone wording was found on {_page_url(page)}.",
                "A contact page that only describes contacting the organization does not provide a clear continuation path.",
                "Expose a working form, email address, phone number, or equivalent concrete contact mechanism.",
            ))

    return findings


def engagement_stub(url: str) -> list[dict[str, Any]]:
    """Compatibility shim for callers that explicitly disable engagement."""
    return []