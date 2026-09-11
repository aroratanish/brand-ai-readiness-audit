"""Dependency-free deterministic Engagement Audit checks (EN-01 to EN-12).

The P3 adapter/orchestrator must map the repository's real PageResult into the
logical fields used here.

This module checks supplied evidence only. It does not crawl, infer unsupported
facts, classify intent from keywords, orchestrate, or deduplicate findings.
"""

from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import urljoin


SOURCE = "engagement-audit"
CATEGORY = "engagement"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _items(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _status(value: Any) -> int | None:
    try:
        return None if value in (None, "") else int(value)
    except (TypeError, ValueError):
        return None


def _finding(
    page: Mapping[str, Any],
    check_id: str,
    title: str,
    evidence: str,
    severity: str,
    why_it_matters: str,
    suggested_action: str,
) -> dict[str, str]:
    return {
        "id": check_id,
        "source_skill": SOURCE,
        "url": _text(page.get("url")),
        "category": CATEGORY,
        "title": title,
        "severity": severity,
        "evidence": evidence,
        "why_it_matters": why_it_matters,
        "suggested_action": suggested_action,
    }


def _high_intent(page: Mapping[str, Any]) -> bool:
    """Trust only the adapter's explicit deterministic high-intent signal."""
    return page.get("high_intent") is True


def _ctas(page: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        c
        for c in _items(page.get("ctas"))
        if isinstance(c, dict)
        and _text(c.get("text") or c.get("label"))
    ]


def _has_action_route(page: Mapping[str, Any]) -> bool:
    return any(
        _text(page.get(field))
        for field in (
            "contact_path",
            "booking_path",
            "purchase_path",
            "demo_path",
            "application_path",
            "support_path",
        )
    )


def _has_text_context(action: Mapping[str, Any]) -> bool:
    if isinstance(action.get("textual_context"), bool):
        return action["textual_context"]

    if action.get("machine_readable") is True:
        return True

    return any(
        _text(action.get(field))
        for field in (
            "accessible_name",
            "aria_label",
            "label",
            "text",
            "description",
            "structured_label",
        )
    )


def check_primary_cta(page: Mapping[str, Any]) -> dict[str, str] | None:
    """EN-01 — Primary CTA / next action presence."""
    if not _high_intent(page):
        return None

    if _ctas(page) or _has_action_route(page):
        return None

    return _finding(
        page,
        "EN-01",
        "No identifiable next action on a high-intent page",
        (
            f"Page intent is '{_text(page.get('intent'))}', but no actionable "
            "CTA or equivalent action route was extracted."
        ),
        "medium",
        "The decision-oriented journey has no deterministically identified next action.",
        "Expose a clear action appropriate to the established page intent.",
    )


def check_cta_targets(page: Mapping[str, Any]) -> list[dict[str, str]]:
    """EN-02 — CTA reachability."""
    base_url = _text(page.get("url"))
    findings = []

    for cta in _ctas(page):
        if cta.get("important") is not True:
            continue

        target = _text(cta.get("target") or cta.get("url"))
        status = _status(cta.get("status"))

        if not target or status is None or status < 400:
            continue

        target = urljoin(base_url, target)

        findings.append(
            _finding(
                page,
                "EN-02",
                "Important CTA target is unreachable",
                (
                    f"CTA '{_text(cta.get('text') or cta.get('label'))}' "
                    f"targets {target} and returned HTTP {status}."
                ),
                "high",
                "The important customer action cannot reach its destination.",
                "Repair or replace the CTA target and verify the action path.",
            )
        )

    return findings


def check_cta_clarity(page: Mapping[str, Any]) -> list[dict[str, str]]:
    """EN-03 — Material CTA ambiguity or destination mismatch."""
    findings = []

    for cta in _ctas(page):
        mismatch = cta.get("mismatch") is True
        ambiguity = (
            cta.get("ambiguity") is True
            or cta.get("clarity_issue") is True
        )

        if not mismatch and not ambiguity:
            continue

        label = _text(cta.get("text") or cta.get("label"))
        purpose = _text(cta.get("target_purpose"))

        if mismatch and purpose:
            reason = (
                f"CTA '{label}' materially conflicts with target purpose "
                f"'{purpose}'."
            )
        else:
            reason = (
                f"CTA '{label}' is explicitly marked as materially ambiguous."
            )

        findings.append(
            _finding(
                page,
                "EN-03",
                "CTA wording does not clearly represent its action",
                reason,
                "high",
                (
                    "The action may cause a visitor or AI agent to select "
                    "the wrong or indeterminate next step."
                ),
                "Make the CTA explicit and consistent with its destination.",
            )
        )

    return findings


def check_value_proposition(
    page: Mapping[str, Any],
) -> dict[str, str] | None:
    """EN-04 — Value proposition clarity."""
    if not _high_intent(page):
        return None

    if _text(page.get("value_proposition")):
        return None

    return _finding(
        page,
        "EN-04",
        "Offering or intended use is not identifiable from direct page content",
        (
            "No normalized value proposition was extracted from directly "
            "observable page content."
        ),
        "medium",
        (
            "The visitor or AI agent may not be able to establish what the "
            "offering is for before continuing."
        ),
        "Expose a concise, directly extractable offering and use description.",
    )


def check_decision_information(
    page: Mapping[str, Any],
) -> dict[str, str] | None:
    """EN-05 — Required decision information."""
    if not _high_intent(page):
        return None

    required = {
        _text(item)
        for item in _items(page.get("required_facts"))
        if _text(item)
    }

    missing = {
        _text(item)
        for item in _items(page.get("missing_facts"))
        if _text(item)
    }

    missing &= required

    if not missing:
        return None

    return _finding(
        page,
        "EN-05",
        "Important decision information is missing",
        (
            "Explicitly required decision facts not found: "
            + ", ".join(sorted(missing))
            + "."
        ),
        "medium",
        (
            "The intended decision may require leaving the journey to obtain "
            "essential information."
        ),
        "Expose the missing decision facts or provide a direct path to them.",
    )


def check_contact_action_path(
    page: Mapping[str, Any],
) -> dict[str, str] | None:
    """EN-06 — Context-appropriate core-service action path."""
    if page.get("core_service") is not True:
        return None

    intent = _text(page.get("intent")).lower()
    if not intent:
        return None

    route_map = {
        "purchase": "purchase_path",
        "buy": "purchase_path",
        "checkout": "purchase_path",
        "booking": "booking_path",
        "book": "booking_path",
        "demo": "demo_path",
        "contact": "contact_path",
        "quote": "contact_path",
        "application": "application_path",
        "apply": "application_path",
        "support": "support_path",
    }

    expected = next(
        (
            key
            for key in route_map
            if key in intent
        ),
        None,
    )

    if expected is None:
        return None

    if _text(page.get(route_map[expected])):
        return None

    for cta in _ctas(page):
        purpose = " ".join(
            _text(cta.get(field)).lower()
            for field in (
                "action_type",
                "text",
                "label",
                "target_purpose",
            )
        )

        if expected in purpose:
            return None

    return _finding(
        page,
        "EN-06",
        "Core journey has no context-appropriate action path",
        (
            f"Core-service page intent is '{_text(page.get('intent'))}', "
            "but no matching action route or CTA was extracted."
        ),
        "high",
        (
            "The visitor or AI agent can reach the journey but cannot reach "
            "its appropriate next action."
        ),
        "Expose a discoverable action path matching the established intent.",
    )


def check_form_actionability(
    page: Mapping[str, Any],
) -> list[dict[str, str]]:
    """EN-07 — Important form actionability."""
    findings = []

    for form in _items(page.get("forms")):
        if not isinstance(form, dict):
            continue

        if form.get("important") is not True:
            continue

        missing = []

        if form.get("purpose_clear") is False:
            missing.append("clear purpose")

        if form.get("submit_control") is False:
            missing.append("submit control")

        if (
            form.get("requires_target") is True
            and not _text(form.get("target"))
        ):
            missing.append("submission target")

        if form.get("submission_path_usable") is False:
            missing.append("usable submission path")

        if not missing:
            continue

        findings.append(
            _finding(
                page,
                "EN-07",
                "Important form lacks an understandable action path",
                "Missing form signals: " + ", ".join(missing) + ".",
                "medium",
                (
                    "The form may prevent the intended action from being "
                    "understood or completed."
                ),
                (
                    "Make the form purpose and required submission path "
                    "explicit and usable."
                ),
            )
        )

    return findings


def check_follow_up_path(
    page: Mapping[str, Any],
) -> dict[str, str] | None:
    """EN-08 — Required follow-up information path."""
    if page.get("follow_up_expected") is not True:
        return None

    links = [
        item
        for item in _items(page.get("follow_up_links"))
        if (
            (not isinstance(item, dict) and _text(item))
            or (
                isinstance(item, dict)
                and any(
                    _text(item.get(field))
                    for field in ("url", "text", "label")
                )
            )
        )
    ]

    if links:
        return None

    return _finding(
        page,
        "EN-08",
        "No useful follow-up information path was found",
        (
            "Follow-up is explicitly required, but no FAQ, help, "
            "documentation, support, or equivalent path was extracted."
        ),
        "medium",
        (
            "Predictable follow-up questions may leave the visitor or "
            "AI agent at a dead end."
        ),
        (
            "Provide a relevant FAQ, help, documentation, support, "
            "or equivalent path."
        ),
    )


def check_stable_direct_url(
    page: Mapping[str, Any],
) -> list[dict[str, str]]:
    """EN-09 — Stable direct representation for opaque actions."""
    findings = []

    for action in _items(page.get("actions")):
        if not isinstance(action, dict):
            continue

        if action.get("important") is not True:
            continue

        if action.get("opaque_interaction") is not True:
            continue

        if _text(
            action.get("direct_target")
            or action.get("target")
            or action.get("url")
        ):
            continue

        if action.get("direct_representation") is True:
            continue

        findings.append(
            _finding(
                page,
                "EN-09",
                "Important action lacks a stable direct target",
                (
                    "An important action is explicitly marked opaque, with "
                    "no direct target or equivalent direct representation."
                ),
                "medium",
                (
                    "The action may be difficult to discover or reproduce "
                    "reliably."
                ),
                (
                    "Expose a stable URL or equivalent machine-readable "
                    "representation."
                ),
            )
        )

    return findings


def check_content_action_consistency(
    page: Mapping[str, Any],
) -> dict[str, str] | None:
    """EN-10 — Page promise versus destination/action purpose."""
    if page.get("action_mismatch") is not True:
        return None

    promise = _text(page.get("page_promise"))
    purpose = _text(page.get("destination_purpose"))

    if not promise or not purpose:
        return None

    return _finding(
        page,
        "EN-10",
        "Page promise and action destination are inconsistent",
        (
            f"Page promise: '{promise}'. "
            f"Destination purpose: '{purpose}'. "
            "Normalized evidence marks them materially inconsistent."
        ),
        "high",
        (
            "The visitor or AI agent may be routed away from the action "
            "promised by the page."
        ),
        "Align the page promise and destination purpose.",
    )


def check_action_context(
    page: Mapping[str, Any],
) -> list[dict[str, str]]:
    """EN-11 — Textual or machine-readable context for important actions."""
    findings = []

    for action in _items(page.get("actions")):
        if not isinstance(action, dict):
            continue

        if action.get("important") is not True:
            continue

        if action.get("visual_only") is not True:
            continue

        if _has_text_context(action):
            continue

        findings.append(
            _finding(
                page,
                "EN-11",
                "Important action lacks textual or machine-readable context",
                (
                    "An important action is explicitly visual-only and has "
                    "no equivalent textual, accessibility, or machine-readable context."
                ),
                "medium",
                (
                    "A text-based or AI interface may be unable to identify "
                    "the action."
                ),
                (
                    "Provide an accessible name, text label, structured "
                    "description, or equivalent machine-readable context."
                ),
            )
        )

    return findings


def check_conversion_path(
    page: Mapping[str, Any],
) -> dict[str, str] | None:
    """EN-12 — Explicitly established journey completeness."""
    required = [
        _text(item)
        for item in _items(page.get("required_steps"))
        if _text(item)
    ]

    available = {
        _text(item)
        for item in _items(page.get("available_steps"))
        if _text(item)
    }

    if not required:
        return None

    missing = [step for step in required if step not in available]

    if not missing:
        return None

    return _finding(
        page,
        "EN-12",
        "Conversion path is missing a required step",
        (
            "Required journey steps not represented: "
            + ", ".join(missing)
            + "."
        ),
        "high",
        (
            "A required step between intent, decision information, and "
            "action is not represented."
        ),
        "Expose the missing journey step and verify the complete path.",
    )


def run_checks(page: Mapping[str, Any]) -> list[dict[str, str]]:
    """Run EN-01 through EN-12 and return canonical findings."""
    results: list[dict[str, str]] = []

    checks = (
        check_primary_cta,
        check_cta_targets,
        check_cta_clarity,
        check_value_proposition,
        check_decision_information,
        check_contact_action_path,
        check_form_actionability,
        check_follow_up_path,
        check_stable_direct_url,
        check_content_action_consistency,
        check_action_context,
        check_conversion_path,
    )

    for check in checks:
        result = check(page)

        if isinstance(result, list):
            results.extend(result)
        elif result is not None:
            results.append(result)

    return results


if __name__ == "__main__":
    import json
    import sys

    page = json.load(sys.stdin)
    print(json.dumps(run_checks(page), indent=2))
