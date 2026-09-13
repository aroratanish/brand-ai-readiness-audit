"""Integrated deterministic checks used by the Round 3 entrypoint.

The module deliberately uses only evidence already collected by the crawler.
It does not call external LLMs or mutate the audited site.
"""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from shared.severity_policy import normalize_severity
from skills.crawl_render_audit.scripts.models import PageResult

SOURCE = "audit-orchestrator"


def _id(code: str, url: str, extra: str = "") -> str:
    digest = hashlib.sha1(f"{url}|{extra}".encode()).hexdigest()[:10]
    return f"F-INT-{code}-{digest}"


def finding(url: str, code: str, title: str, severity: str, evidence: str,
            why: str, action: str, category: str, confidence: str = "high") -> dict:
    sev = normalize_severity(severity)
    return {
        "id": _id(code, url, title), "source_skill": SOURCE, "url": url,
        "category": category, "title": title, "severity": sev,
        "confidence": confidence, "evidence": evidence,
        "why_it_matters": why,
        "suggested_action": {"summary": action, "priority": sev},
    }


def technical_findings(page: PageResult) -> list[dict]:
    """Turn existing technical analyzer evidence into actionable findings."""
    url = page.final_url or page.url
    evidence = page.technical_evidence or {}
    findings = []
    metadata = {x.get("check"): x for x in evidence.get("metadata", []) if isinstance(x, dict)}

    title = metadata.get("title", {})
    if title.get("status") in {"too_short", "too_long"}:
        length = title.get("evidence", {}).get("observed_length")
        findings.append(finding(url, "TITLE-LENGTH", "Page title is outside the recommended range", "low",
            f"Title length is {length} characters on {url}; analyzer range is 10–60.",
            "Extreme title lengths can reduce clarity in search and machine-generated summaries.",
            "Rewrite the title to be concise, descriptive, and specific to the page.", "discoverability", "high"))

    desc = metadata.get("meta_description", {})
    if desc.get("status") in {"too_short", "too_long"}:
        length = desc.get("evidence", {}).get("observed_length")
        findings.append(finding(url, "DESC-LENGTH", "Meta description is outside the recommended range", "low",
            f"Meta description length is {length} characters on {url}; analyzer range is 50–160.",
            "Descriptions outside a practical range may provide weak context for search and AI summaries.",
            "Rewrite the description to summarize the page and its useful context in roughly 50–160 characters.", "discoverability", "high"))

    canonical = evidence.get("canonical", {})
    if canonical.get("status") == "invalid":
        findings.append(finding(url, "CANONICAL-INVALID", "Canonical URL is invalid", "high",
            f"Canonical value {canonical.get('evidence', {}).get('observed_canonical')!r} could not be normalized.",
            "An invalid canonical does not reliably identify the preferred page URL.",
            "Replace it with a valid absolute or resolvable canonical URL.", "discoverability", "high"))
    elif canonical.get("status") == "cross_domain":
        findings.append(finding(url, "CANONICAL-CROSS", "Canonical points to another domain", "high",
            f"Page host is {canonical.get('evidence', {}).get('page_host')!r}, canonical host is {canonical.get('evidence', {}).get('canonical_host')!r}.",
            "A cross-domain canonical can cause the current page to be treated as a secondary representation of another site.",
            "Confirm the cross-domain relationship is intentional; otherwise use the site's intended canonical URL.", "discoverability", "high"))

    jsonld = evidence.get("json_ld", {})
    if jsonld.get("evidence", {}).get("invalid_blocks", 0) > 0:
        findings.append(finding(url, "JSONLD-INVALID-BLOCK", "Some JSON-LD blocks are invalid", "medium",
            f"JSON-LD analyzer found {jsonld['evidence']['invalid_blocks']} invalid block(s) out of {jsonld['evidence'].get('total_blocks', 0)}.",
            "Invalid structured data can remove machine-readable context that assistants and search systems could otherwise use.",
            "Remove or repair invalid JSON-LD and validate the resulting structured data.", "structured-data", "high"))

    # Link-level failures are direct evidence because the crawler records the
    # actual response classification for each checked link.
    for link in getattr(page, "link_results", []) or []:
        if getattr(link, "classification", "") in {"client_error", "server_error", "request_error"}:
            findings.append(finding(url, "BROKEN-LINK", "Page contains a broken or unreachable link", "high" if getattr(link, "classification", "") == "server_error" else "medium",
                f"Link {getattr(link, 'url', '')} returned classification {getattr(link, 'classification', '')!r} with status {getattr(link, 'status_code', None)!r}.",
                "Broken destinations interrupt both visitor journeys and machine discovery paths.",
                "Repair the destination, remove the link, or redirect it to the intended live resource.", "crawlability", "high"))

    render = evidence.get("render", {})
    if render.get("status") == "error":
        findings.append(finding(url, "RENDER-FAIL", "Browser rendering failed for a crawled HTML page", "medium",
            f"Renderer error for {url}: {render.get('evidence', {}).get('error', 'unknown error')}.",
            "A render failure limits the audit's ability to verify client-rendered content and can also indicate fragile rendering dependencies.",
            "Investigate the client-side rendering error and keep essential content available in the initial HTML where practical.", "discoverability", "high"))

    return findings


def _visible_text(page: PageResult, rendered: bool = False) -> str:
    html = page.rendered_html if rendered else page.raw_html
    soup = BeautifulSoup(html or "", "lxml")
    for el in soup(["script", "style", "noscript", "template", "svg"]):
        el.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def _page_type(page: PageResult) -> str:
    path = urlparse(page.final_url or page.url).path.lower().rstrip("/") or "/"
    types = page.technical_evidence.get("page_type", {}) if page.technical_evidence else {}
    if isinstance(types, dict) and types.get("type"):
        return types["type"]
    patterns = {
        "product": r"/(products?|items?)(/|$)", "pricing": r"/(pricing|plans?|price)(/|$)",
        "contact": r"/(contact|contact-us)(/|$)", "about": r"/(about|about-us|company)(/|$)",
        "faq": r"/(faq|faqs)(/|$)", "article": r"/(blog|article|articles|news|posts?)(/|$)",
        "documentation": r"/(docs?|documentation|help|guides?)(/|$)",
    }
    for kind, pattern in patterns.items():
        if re.search(pattern, path): return kind
    return "homepage" if page.depth == 0 else "general"


def render_semantic_findings(page: PageResult) -> list[dict]:
    """Only flag render-only changes when the added content looks materially important."""
    diff = (page.technical_evidence or {}).get("raw_vs_rendered", {})
    if diff.get("status") != "rendered_content_added": return []
    sample = str(diff.get("evidence", {}).get("rendered_only_sample", ""))
    words = len(sample.split())
    important = re.search(r"\b(price|pricing|buy|book|contact|demo|trial|quote|available|availability|shipping|return|refund|plan|service|product|email|phone|address)\b", sample, re.I)
    if not important and words < 25: return []
    url = page.final_url or page.url
    return [finding(url, "RENDER-IMPORTANT", "Important content appears only after rendering", "high",
        f"Rendered-only sample contains potentially decision-relevant content: {sample[:300]!r}.",
        "Simple readers may inspect initial HTML without executing JavaScript and miss decision-relevant facts or actions.",
        "Server-render key facts, prices, availability, identity, and primary actions; use JavaScript as progressive enhancement.", "discoverability", "high")]


def answerability_findings(page: PageResult) -> list[dict]:
    """Deterministic answerability checks for high-intent page types."""
    url = page.final_url or page.url
    text = _visible_text(page)
    lower = text.lower()
    kind = _page_type(page)
    findings = []
    if kind in {"product", "pricing"}:
        has_action = bool(re.search(r"\b(buy|book|contact|demo|trial|quote|subscribe|get started|start)\b", lower))
        has_value = len(text.split()) >= 35
        if not has_value and has_action:
            findings.append(finding(url, "ANSWERABILITY", "High-intent page has an action but limited answer context", "medium",
                f"Classified as {kind}; visible text has only {len(text.split())} words while actionable language is present.",
                "An AI-referred visitor may arrive at a conversion action without enough context to understand the offer, audience, or outcome.",
                "Add a concise description of the offering, audience, key decision facts, and what happens after the primary action.", "discoverability", "medium"))
    return findings


def site_fact_findings(pages: list[PageResult]) -> list[dict]:
    """Compare first-party structured facts conservatively."""
    findings=[]; orgs=defaultdict(list); phones=defaultdict(list); emails=defaultdict(list)
    products=defaultdict(list)
    for p in pages:
        url=p.final_url or p.url
        for obj in _iter_jsonld(p.json_ld):
            types=_types(obj)
            if types & {"organization","corporation"} and isinstance(obj.get("name"),str): orgs[_norm(obj["name"])].append((url,obj["name"]))
            if types & {"product"} and isinstance(obj.get("name"),str):
                offers=obj.get("offers",{}); offers=offers if isinstance(offers,list) else [offers]
                for offer in offers:
                    if isinstance(offer,dict) and offer.get("price") is not None:
                        products[_norm(obj["name"])].append((url,obj["name"],str(offer["price"]),str(offer.get("priceCurrency", ""))))
    all_org_names={name for entries in orgs.values() for _,name in entries}
    names=list(all_org_names)
    for i,a in enumerate(names):
        for b in names[i+1:]:
            na,nb=_norm(a),_norm(b)
            if na != nb and SequenceMatcher(None,na,nb).ratio() < .72 and na not in nb and nb not in na:
                urls="; ".join(f"{n!r} ({u})" for n,u in [(a,orgs[_norm(a)][0][0]),(b,orgs[_norm(b)][0][0])])
                findings.append(finding(orgs[_norm(a)][0][0],"ORG-CONFLICT","Conflicting organization identities appear across the site","high",urls,
                    "Conflicting first-party identity signals can cause AI systems to merge, split, or misattribute the brand entity.",
                    "Choose a canonical organization identity and represent intentional aliases with explicit Brand/Organization relationships.","entity-trust","high")); break
    for key, entries in products.items():
        vals={(price,currency.lower()) for _,_,price,currency in entries}
        if len(vals)>1:
            sample="; ".join(f"{name!r}: {price} {currency} ({url})" for url,name,price,currency in entries[:6])
            findings.append(finding(entries[0][0],"PRODUCT-PRICE-CONFLICT","Product prices conflict across first-party pages","high",sample,
                "An AI system may quote a stale or incorrect commercial fact when first-party pages disagree.",
                "Create a single current offer source and synchronize visible text, structured data, and related pages.","freshness","high"))
    # Policy pages with an explicit old visible year are surfaced as review
    # signals, never as proof of stale policy content.
    for p in pages:
        policy_url = p.final_url or p.url
        if not re.search(r"/(privacy|terms|policy|policies|returns?|refunds?)(/|$)", urlparse(policy_url).path.lower()):
            continue
        policy_text = _visible_text(p)
        years=[int(y) for y in re.findall(r"\b(20\d{2})\b", policy_text)]
        if years and max(years) < datetime.now(timezone.utc).year - 2:
            findings.append(finding(policy_url,"POLICY-REVIEW","Policy page contains an old explicit year that merits review","low",
                f"Policy-like URL contains year(s) {sorted(set(years))[-3:]} while current audit year is {datetime.now(timezone.utc).year}.",
                "Old visible years on policy pages can make current terms appear stale, although a year alone does not prove the policy is outdated.",
                "Review the policy and update dates only if the underlying policy has changed.","freshness","medium"))
    return findings


def _iter_jsonld(value):
    if isinstance(value,list):
        for x in value: yield from _iter_jsonld(x)
    elif isinstance(value,dict):
        yield value
        if isinstance(value.get("@graph"),(list,dict)): yield from _iter_jsonld(value["@graph"])

def _types(obj):
    t=obj.get("@type") if isinstance(obj,dict) else None
    if isinstance(t,str): return {t.lower()}
    if isinstance(t,list): return {x.lower() for x in t if isinstance(x,str)}
    return set()

def _norm(x): return re.sub(r"[^a-z0-9]+"," ",str(x).lower()).strip()


def freshness_enhanced(page: PageResult, as_of: datetime | None = None) -> list[dict]:
    """Additional freshness checks that avoid treating missing dates as stale."""
    url=page.final_url or page.url; findings=[]; now=as_of or datetime.now(timezone.utc)
    text=_visible_text(page)
    for obj in _iter_jsonld(page.json_ld):
        types=_types(obj)
        if "product" in types:
            for offer in ([obj.get("offers")] if isinstance(obj.get("offers"),dict) else obj.get("offers",[])):
                if not isinstance(offer,dict): continue
                availability=str(offer.get("availability","")).lower()
                if "outofstock" in availability and re.search(r"\b(buy|available|in stock|add to cart)\b",text,re.I):
                    findings.append(finding(url,"AVAILABILITY-CONFLICT","Structured availability conflicts with visible action language","high",
                        f"Structured data says {offer.get('availability')!r}, while visible page text contains availability/purchase language.",
                        "Conflicting availability signals can cause assistants to recommend an unavailable offer.",
                        "Synchronize structured availability with the current visible offer state.","freshness","high"))
        for field in ("dateModified","datePublished"):
            value=obj.get(field)
            if isinstance(value,str):
                try:
                    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
                    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
                    if (now-dt).days>365 and "article" not in types and "newsarticle" not in types and "blogposting" not in types:
                        findings.append(finding(url,"STALE-SIGNAL",f"{field} is older than one year","medium",
                            f"JSON-LD {field} is {value!r} on {url}.",
                            "A stale modification signal can reduce confidence that current operational information is maintained.",
                            f"Review whether {field} is still accurate; update it only when the underlying content has actually changed.","freshness","high"))
                except ValueError: pass
    return findings
