"""Dependency-free deterministic Engagement Audit checks.

Input:
    A normalized engagement page dictionary produced by the upstream
    PageResult adapter.

Output:
    Check-level findings. The adapter/provider is responsible for converting
    these records into the repository's canonical Finding contract.

Rules:
    - Observable evidence only.
    - UNKNOWN is not equivalent to absent or failed.
    - Classification flags must be explicit booleans.
    - Do not fabricate intent, required facts, journey steps, or action failures.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin


def _text(value: Any) -> str:
    return str(value or "").strip()


def _is_true(value: Any) -> bool:
    return value is True


def _nonempty(value: Any) -> bool:
    return bool(_text(value))


def _nonempty_collection(value: Any) -> bool:
    return isinstance(value, (list, tuple, set)) and bool(value)


def _finding(
    check_id: str,
    title: str,
    evidence: str,
    severity: str,
) -> dict[str, str]:
    return {
        "check_id": check_id,
        "title": title,
        "evidence": evidence,
        "severity": severity,
    }


def _action_items(page: dict[str, Any]) -> list[dict[str, Any]]:
    value = page.get("actions") or []
    return [item for item in value if isinstance(item, dict)]


def _cta_items(page: dict[str, Any]) -> list[dict[str, Any]]:
    value = page.get("ctas") or []
    return [item for item in value if isinstance(item, dict)]


def _has_actionable_cta(page: dict[str, Any]) -> bool:
    for cta in _cta_items(page):
        if not _text(cta.get("text")):
            continue

        if cta.get("actionable") is False:
            continue

        return True

    return False


def check_primary_cta(page: dict[str, Any]) -> dict[str, str] | None:
    """EN-01: high-intent pages need an appropriate next action."""

    if not _is_true(page.get("high_intent")):
        return None

    if _has_actionable_cta(page):
        return None

    return _finding(
        "EN-01",
        "No identifiable next action on a high-intent page",
        (
            f"Page '{_text(page.get('url'))}' is explicitly classified as "
            f"high-intent for intent '{_text(page.get('intent'))}', but no "
            "actionable CTA was extracted."
        ),
        "medium",
    )


def check_cta_targets(page: dict[str, Any]) -> list[dict[str, str]]:
    """EN-02: important CTA targets must be demonstrably unreachable."""

    findings: list[dict[str, str]] = []
    base = _text(page.get("url"))

    for cta in _cta_items(page):
        if cta.get("important") is False:
            continue

        status = cta.get("status")

        if status is None:
            continue

        try:
            status_code = int(status)
        except (TypeError, ValueError):
            continue

        if status_code < 400:
            continue

        raw_target = _text(cta.get("target"))

        target = (
            urljoin(base, raw_target)
            if raw_target
            else "<unknown target>"
        )

        findings.append(
            _finding(
                "EN-02",
                "Important action target is unreachable",
                (
                    f"CTA '{_text(cta.get('text'))}' targets {target} "
                    f"and returned HTTP {status_code}."
                ),
                "high",
            )
        )

    return findings


def check_cta_clarity(page: dict[str, Any]) -> list[dict[str, str]]:
    """EN-03: CTA wording must materially match destination purpose."""

    findings: list[dict[str, str]] = []

    for cta in _cta_items(page):
        if not _is_true(cta.get("mismatch")):
            continue

        purpose = _text(cta.get("target_purpose"))
        label = _text(cta.get("text"))

        if not purpose or not label:
            continue

        findings.append(
            _finding(
                "EN-03",
                "CTA wording materially conflicts with destination",
                (
                    f"CTA '{label}' is deterministically marked as materially "
                    f"mismatched with destination purpose '{purpose}'."
                ),
                "high",
            )
        )

    return findings


def check_value_proposition(
    page: dict[str, Any],
) -> dict[str, str] | None:
    """EN-04: high-intent pages need directly observable offering context."""

    if not _is_true(page.get("high_intent")):
        return None

    if _nonempty(page.get("value_proposition")):
        return None

    # Do not flag merely because the adapter did not collapse richer
    # extracted evidence into value_proposition.
    if _nonempty(page.get("offering_context")):
        return None

    return _finding(
        "EN-04",
        "Offering is not identifiable from direct page content",
        (
            f"High-intent page '{_text(page.get('url'))}' has no extracted "
            "offering/audience/use context in the supplied evidence."
        ),
        "medium",
    )


def check_decision_information(
    page: dict[str, Any],
) -> dict[str, str] | None:
    """EN-05: explicitly required decision facts must be evidenced."""

    if not _is_true(page.get("high_intent")):
        return None

    required = page.get("required_facts")
    missing = page.get("missing_facts")

    if not isinstance(required, (list, tuple, set)):
        return None

    if not isinstance(missing, (list, tuple, set)):
        return None

    if not required:
        return None

    required = [
        str(x).strip()
        for x in required
        if str(x).strip()
    ]

    missing = [
        str(x).strip()
        for x in missing
        if str(x).strip()
    ]

    if not required or not missing:
        return None

    evidence_for_requirement = page.get("evidence_for_requirement")

    if evidence_for_requirement is None:
        return None

    return _finding(
        "EN-05",
        "Important decision information is missing",
        (
            f"Required journey facts: {', '.join(required)}. "
            f"Missing from inspected evidence: {', '.join(missing)}. "
            f"Requirement evidence: {_text(evidence_for_requirement)}"
        ),
        "medium",
    )


def _expected_action_route(page: dict[str, Any]) -> Any:
    expected = _text(page.get("expected_action")).lower()

    routes = {
        "contact": page.get("contact_path"),
        "sales": page.get("contact_path"),
        "contact_sales": page.get("contact_path"),
        "booking": page.get("booking_path"),
        "book": page.get("booking_path"),
        "purchase": page.get("purchase_path"),
        "buy": page.get("purchase_path"),
        "demo": page.get("demo_path"),
        "trial": page.get("action_path"),
        "signup": page.get("action_path"),
        "application": page.get("action_path"),
        "quote": page.get("action_path"),
        "support": page.get("support_path"),
    }

    if expected in routes:
        return routes[expected]

    return page.get("action_path")


def check_contact_action_path(
    page: dict[str, Any],
) -> dict[str, str] | None:
    """EN-06: core-service journeys need an appropriate action route."""

    if not _is_true(page.get("core_service")):
        return None

    if not _text(page.get("expected_action")):
        return None

    route = _expected_action_route(page)

    if _nonempty(route) or _nonempty_collection(route):
        return None

    return _finding(
        "EN-06",
        "Core service has no discoverable action path",
        (
            f"Core-service page '{_text(page.get('url'))}' has expected action "
            f"'{_text(page.get('expected_action'))}', but no appropriate "
            "contact, booking, purchase, demo, application, support or "
            "equivalent route was extracted."
        ),
        "high",
    )


def check_form_actionability(
    page: dict[str, Any],
) -> list[dict[str, str]]:
    """EN-07: important forms need an understandable submission path."""

    findings: list[dict[str, str]] = []

    for form in page.get("forms") or []:
        if not isinstance(form, dict):
            continue

        if not _is_true(form.get("important")):
            continue

        missing: list[str] = []

        if not _is_true(form.get("purpose_clear")):
            missing.append("clear purpose")

        if not _is_true(form.get("submit_control")):
            missing.append("submit control")

        if (
            _is_true(form.get("requires_target"))
            and not _text(form.get("target"))
        ):
            missing.append("required submission target")

        if form.get("execution_result") == "failed":
            missing.append("successful submission execution")

        if not missing:
            continue

        findings.append(
            _finding(
                "EN-07",
                "Important form lacks a usable submission path",
                (
                    f"Important form on '{_text(page.get('url'))}' is missing "
                    f"deterministic signals: {', '.join(missing)}."
                ),
                "medium",
            )
        )

    return findings


def check_follow_up_path(
    page: dict[str, Any],
) -> dict[str, str] | None:
    """EN-08: established required follow-up needs a discoverable path."""

    if not _is_true(page.get("follow_up_expected")):
        return None

    if _nonempty_collection(page.get("follow_up_links")):
        return None

    return _finding(
        "EN-08",
        "Required follow-up path is missing",
        (
            f"Journey on '{_text(page.get('url'))}' explicitly requires "
            "follow-up information/action, but no relevant follow-up path "
            "was discovered."
        ),
        "medium",
    )


def check_stable_direct_url(
    page: dict[str, Any],
) -> dict[str, str] | None:
    """EN-09: genuinely opaque important actions need a usable representation."""

    if not _is_true(page.get("important_action")):
        return None

    if not _is_true(page.get("opaque_interaction")):
        return None

    if _text(page.get("direct_target")):
        return None

    if _is_true(page.get("action_identifiable")):
        return None

    return _finding(
        "EN-09",
        "Important action is genuinely opaque",
        (
            f"Important action on '{_text(page.get('url'))}' is explicitly "
            "classified as opaque, has no usable direct target, and cannot "
            "be deterministically identified/invoked from the supplied evidence."
        ),
        "medium",
    )


def check_content_action_consistency(
    page: dict[str, Any],
) -> dict[str, str] | None:
    """EN-10: page promise must materially match action/destination purpose."""

    if not _is_true(page.get("action_mismatch")):
        return None

    promise = _text(page.get("page_promise"))
    purpose = _text(page.get("destination_purpose"))

    if not promise or not purpose:
        return None

    return _finding(
        "EN-10",
        "Page promise and action destination are inconsistent",
        (
            f"Page promise is '{promise}', while the destination/action "
            f"purpose is '{purpose}'. The adapter marked this as a material "
            "mismatch."
        ),
        "high",
    )


def check_action_context(
    page: dict[str, Any],
) -> dict[str, str] | None:
    """EN-11: important actions need machine-readable textual context."""

    missing_context = []

    for action in _action_items(page):
        if not _is_true(action.get("important")):
            continue

        if not _is_true(action.get("visual_only")):
            continue

        context_present = any(
            _text(action.get(field))
            for field in (
                "text",
                "text_context",
                "link_context",
                "accessibility_context",
                "structured_context",
            )
        )

        if not context_present:
            missing_context.append(action)

    if not missing_context:
        return None

    return _finding(
        "EN-11",
        "Important action lacks AI-readable context",
        (
            f"{len(missing_context)} important action(s) on "
            f"'{_text(page.get('url'))}' are deterministically visual/"
            "interaction-dependent and have no equivalent textual, link, "
            "accessibility or structured representation."
        ),
        "medium",
    )


def check_conversion_path(
    page: dict[str, Any],
) -> dict[str, str] | None:
    """EN-12: explicitly established journeys must contain required steps."""

    if not _is_true(page.get("conversion_path")):
        return None

    required = page.get("required_steps")
    available = page.get("available_steps")

    if not isinstance(required, (list, tuple, set)):
        return None

    if not isinstance(available, (list, tuple, set)):
        return None

    required = list(required)
    available = set(available)

    if not required:
        return None

    missing = [
        step
        for step in required
        if step not in available
    ]

    if not missing:
        return None

    return _finding(
        "EN-12",
        "Required journey step is missing",
        (
            f"Journey on '{_text(page.get('url'))}' requires steps "
            f"{', '.join(map(str, required))}; missing/inaccessible steps: "
            f"{', '.join(map(str, missing))}."
        ),
        "high",
    )


def run_checks(
    page: dict[str, Any],
) -> list[dict[str, str]]:
    """Run EN-01 through EN-12 against normalized evidence."""

    results: list[dict[str, str]] = []

    results.extend(check_cta_targets(page))
    results.extend(check_cta_clarity(page))
    results.extend(check_form_actionability(page))

    for check in (
        check_primary_cta,
        check_value_proposition,
        check_decision_information,
        check_contact_action_path,
        check_follow_up_path,
        check_stable_direct_url,
        check_content_action_consistency,
        check_action_context,
        check_conversion_path,
    ):
        result = check(page)

        if result is not None:
            results.append(result)

    return results


if __name__ == "__main__":
    import json
    import sys

    payload = json.load(sys.stdin)

    print(
        json.dumps(
            run_checks(payload),
            indent=2,
        )
    )
