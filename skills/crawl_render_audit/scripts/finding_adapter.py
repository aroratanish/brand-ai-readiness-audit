import hashlib

from .models import PageResult
from .entity_analyzer import analyze_entity
from .url_utils import normalize_url
from shared.severity_policy import normalize_severity


SOURCE_SKILL = "crawl-render-audit"


def build_finding(
    finding_id: str,
    url: str,
    category: str,
    title: str,
    severity: str,
    evidence: str,
    why_it_matters: str,
    action_summary: str,
) -> dict:
    """Build a finding using the shared canonical finding structure."""
    normalized_severity = normalize_severity(severity)

    return {
        "id": finding_id,
        "source_skill": SOURCE_SKILL,
        "url": url,
        "category": category,
        "title": title,
        "severity": normalized_severity,
        "evidence": evidence,
        "why_it_matters": why_it_matters,
        "suggested_action": {
            "summary": action_summary,
            "priority": normalized_severity,
        },
    }


def _finding_id(check_code: str, page_url: str) -> str:
    url_digest = hashlib.sha1(
        page_url.encode("utf-8")
    ).hexdigest()[:10]
    return f"F-{check_code}-{url_digest}"


def findings_for_page(page: PageResult) -> list[dict]:
    """Return first-iteration readiness findings for one crawled page."""
    findings = []
    page_url = page.final_url or page.url

    if not page.meta_description:
        findings.append(
            build_finding(
                _finding_id("META-DESC", page_url),
                page_url,
                "discoverability",
                "Missing meta description",
                "medium",
                f"No <meta name='description'> found on {page_url}",
                "Search engines and AI tools rely on this for summaries; without it they generate their own.",
                "Add a concise meta description.",
            )
        )

    if not page.json_ld:
        findings.append(
            build_finding(
                _finding_id("JSON-LD", page_url),
                page_url,
                "structured-data",
                "Missing JSON-LD structured data",
                "medium",
                f"No JSON-LD structured data found on {page_url}",
                "Structured data helps search engines and AI systems interpret important page entities and details.",
                "Add accurate JSON-LD structured data relevant to the page.",
            )
        )

    if not page.canonical:
        findings.append(
            build_finding(
                _finding_id("CANONICAL", page_url),
                page_url,
                "discoverability",
                "Missing canonical",
                "medium",
                f"No canonical link found on {page_url}",
                "A canonical URL helps search engines identify the preferred version of a page and avoid duplicate indexing.",
                "Add a canonical link pointing to the preferred page URL.",
            )
        )
    elif (
        page.final_url
        and normalize_url(page.canonical)
        != normalize_url(page.final_url)
    ):
        findings.append(
            build_finding(
                _finding_id("CANONICAL", page_url),
                page_url,
                "discoverability",
                "Incorrect canonical",
                "medium",
                f"Canonical {page.canonical} does not match effective URL {page.final_url}",
                "An incorrect canonical can cause the preferred page version to be misidentified or excluded from search results.",
                "Review the canonical link and point it to the intended effective page URL.",
            )
        )

    if len(page.h1) == 0:
        findings.append(
            build_finding(
                _finding_id("H1-MISSING", page_url),
                page_url,
                "discoverability",
                "Missing H1 heading",
                "medium",
                f"No H1 heading found on {page_url}",
                "The page lacks a primary heading that helps users, search engines, and AI systems identify its main subject.",
                "Add one clear, descriptive H1 heading.",
            )
        )

    if len(page.h1) > 1:
        findings.append(
            build_finding(
                _finding_id("H1-MULTIPLE", page_url),
                page_url,
                "discoverability",
                "Multiple H1 headings",
                "medium",
                f"Found {len(page.h1)} H1 headings on {page_url}",
                "Multiple competing primary headings can make the page's main topic less clear.",
                "Keep one primary H1 and use lower-level headings for subsections.",
            )
        )

    for heading_level, headings in (("H1", page.h1), ("H2", page.h2)):
        if any(not heading.strip() for heading in headings):
            findings.append(
                build_finding(
                    _finding_id(f"EMPTY-{heading_level}", page_url),
                    page_url,
                    "discoverability",
                    "Empty heading text",
                    "low",
                    f"Empty {heading_level} heading text found on {page_url}",
                    "Empty headings provide no useful structure to users or machine readers.",
                    "Add descriptive heading text or remove the empty heading.",
                )
            )

    if any(
        isinstance(item, dict) and item.get("_parse_error") is True
        for item in page.json_ld
    ):
        findings.append(
            build_finding(
                _finding_id("JSON-LD-MALFORMED", page_url),
                page_url,
                "structured-data",
                "Malformed JSON-LD",
                "medium",
                f"Malformed JSON-LD found on {page_url}",
                "Invalid structured data may prevent search engines and AI systems from interpreting important page information.",
                "Correct the JSON-LD syntax and validate it against the intended schema.",
            )
        )

    entity_signal = analyze_entity(page)
    if entity_signal:
        findings.append(
            build_finding(
                _finding_id("ENTITY-MISMATCH", page_url),
                page_url,
                "entity-trust",
                "Entity identity is inconsistent across page signals",
                "medium",
                (
                    f"Visible identity {entity_signal['visible_name']!r} differs from "
                    f"Organization schema name {entity_signal['schema_name']!r} on {page_url}"
                ),
                "Conflicting identity signals make it harder for AI systems and visitors to determine which organization the page represents.",
                "Align visible branding, metadata, and Organization JSON-LD, or document the relationship between distinct brands.",
            ) | {"confidence": entity_signal["confidence"]}
        )

    evidence = getattr(page, "technical_evidence", {}) or {}
    render_diff = evidence.get("raw_vs_rendered", {})
    if render_diff.get("status") == "rendered_content_added":
        diff_evidence = render_diff.get("evidence", {})
        findings.append(
            build_finding(
                _finding_id("RENDER-ONLY", page_url),
                page_url,
                "discoverability",
                "Important page content appears only after rendering",
                "high",
                (
                    f"Rendered text added {diff_evidence.get('text_delta', 'unknown')} characters "
                    f"on {page_url}; raw HTML does not contain the same visible content"
                ),
                "Some crawlers and AI systems read the initial HTML without executing JavaScript, so important facts may be missed.",
                "Publish essential facts and actions in server-rendered HTML, with JavaScript as an enhancement.",
            )
        )

    if page.status_code is not None and page.status_code >= 400:
        findings.append(
            build_finding(
                _finding_id("HTTP-ERROR", page_url),
                page_url,
                "crawlability",
                "Page returned an HTTP error",
                "high" if page.status_code >= 500 else "medium",
                f"{page_url} returned HTTP {page.status_code}",
                "HTTP errors prevent visitors and machine readers from retrieving the page reliably.",
                "Repair the endpoint or redirect it to the correct live URL, then verify the response status.",
            )
        )

    # internal_links contains URLs only; without per-link response statuses,
    # broken-link findings would be guesses and are intentionally deferred.

    return findings
