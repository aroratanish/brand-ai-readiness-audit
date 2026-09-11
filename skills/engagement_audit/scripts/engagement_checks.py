"""Dependency-free deterministic engagement checks.

The crawler/orchestrator should adapt its real PageResult into the logical
fields listed in SKILL.md. These functions return check-level findings only.

Rules:
- Use observable evidence only.
- UNKNOWN is not equivalent to absent or failed.
- Do not infer high-intent status from a non-empty intent string alone.
- Do not fabricate missing evidence.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin


def _text(value: Any) -> str:
    """Return normalized text."""
    return str(value or "").strip()


def _finding(
    check_id: str,
    title: str,
    evidence: str,
    severity: str,
) -> dict[str, str]:
    """Create a check-level finding."""
    return {
        "check_id": check_id,
        "title": title,
        "evidence": evidence,
        "severity": severity,
    }


def _is_true(value: Any) -> bool:
    """Accept only an explicit boolean True for deterministic flags."""
    return value is True


def _has_cta(page: dict[str, Any]) -> bool:
    """Return True when at least one CTA has observable text."""
    return any(
        isinstance(cta, dict) and _text(cta.get("text"))
        for cta in (page.get("ctas") or [])
    )


def check_primary_cta(page: dict[str, Any]) -> dict[str, str] | None:
    """EN-01: High-intent pages should expose an actionable CTA."""
    # IMPORTANT:
    # A non-empty `intent` is not sufficient to establish high intent.
    if not _is_true(page.get("high_intent")):
        return None

    if _has_cta(page):
        return None

    return _finding(
        "EN-01",
        "No identifiable next action on a high-intent page",
        (
            f"Page intent is '{_text(page.get('intent'))}', "
            "the page is explicitly marked high-intent, "
            "but no actionable CTA was extracted."
        ),
        "medium",
    )


def check_cta_targets(page: dict[str, Any]) -> list[dict[str, str]]:
    """EN-02: Important CTA targets must be demonstrably reachable."""
    base = _text(page.get("url"))
    findings: list[dict[str, str]] = []

    for cta in page.get("ctas") or []:
        if not isinstance(cta, dict):
            continue

        status = cta.get("status")

        # Missing/unknown status is not evidence of failure.
        if status is None:
            continue

        try:
            status_code = int(status)
        except (TypeError, ValueError):
            continue

        if status_code < 400:
            continue

        raw_target = _text(cta.get("target"))

        # We should not manufacture a target URL.
        if not raw_target:
            target = "<unknown target>"
        else:
            target = urljoin(base, raw_target)

        findings.append(
            _finding(
                "EN-02",
                "Core action target is unreachable",
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

    for cta in page.get("ctas") or []:
        if not isinstance(cta, dict):
            continue

        # `mismatch` must be an explicit deterministic adapter result.
        if not _is_true(cta.get("mismatch")):
            continue

        target_purpose = _text(cta.get("target_purpose"))

        if not target_purpose:
            # A mismatch without destination-purpose evidence is not enough.
            continue

        findings.append(
            _finding(
                "EN-03",
                "CTA wording does not match its destination",
                (
                    f"CTA '{_text(cta.get('text'))}' is marked as "
                    f"materially mismatched with target purpose "
                    f"'{target_purpose}'."
                ),
                "high",
            )
        )

    return findings


def check_value_proposition(page: dict[str, Any]) -> dict[str, str] | None:
    """EN-04: High-intent pages need observable offering context."""
    if not _is_true(page.get("high_intent")):
        return None

    if _text(page.get("value_proposition")):
        return None

    return _finding(
        "EN-04",
        "Offering is not identifiable from direct page content",
        (
            "The page is explicitly marked high-intent, but no directly "
            "extracted offering, audience, or use context was provided."
        ),
        "medium",
    )


def check_decision_information(page: dict[str, Any]) -> dict[str, str] | None:
    """EN-05: Required decision facts must be observable."""
    if not _is_true(page.get("high_intent")):
        return None

    missing = page.get("missing_facts") or []

    if not isinstance(missing, (list, tuple, set)):
        return None

    missing = [str(fact).strip() for fact in missing if str(fact).strip()]

    if not missing:
        return None

    return _finding(
        "EN-05",
        "Important decision information is missing",
        (
            "Decision facts established as required for this journey "
            f"were not found in the inspected evidence: {', '.join(missing)}."
        ),
        "medium",
    )


def check_contact_action_path(page: dict[str, Any]) -> dict[str, str] | None:
    """EN-06: Core-service pages need an appropriate action route."""
    if not _is_true(page.get("core_service")):
        return None

    if page.get("action_path"):
        return None

    return _finding(
        "EN-06",
        "Core service has no discoverable action path",
        (
            "The page is explicitly marked as a core-service page, "
            "but no appropriate contact, booking, purchase, demo, "
            "application, or support route was extracted."
        ),
        "high",
    )


def check_form_actionability(page: dict[str, Any]) -> list[dict[str, str]]:
    """EN-07: Important forms need an understandable submission path."""
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

        # Only require a target when the adapter establishes that one
        # is required for this form.
        if _is_true(form.get("requires_target")) and not _text(
            form.get("target")
        ):
            missing.append("submission target")

        if not missing:
            continue

        findings.append(
            _finding(
                "EN-07",
                "Important form lacks an understandable action path",
                f"Missing form signals: {', '.join(missing)}.",
                "medium",
            )
        )

    return findings


def check_follow_up_path(page: dict[str, Any]) -> dict[str, str] | None:
    """EN-08: Required follow-up information needs a discoverable path."""
    if not _is_true(page.get("follow_up_expected")):
        return None

    if page.get("follow_up_links"):
        return None

    return _finding(
        "EN-08",
        "No useful follow-up information path was found",
        (
            "The journey is explicitly marked as requiring predictable "
            "follow-up information, but no relevant FAQ, help, "
            "documentation, or support path was extracted."
        ),
        "medium",
    )


def check_stable_direct_url(page: dict[str, Any]) -> dict[str, str] | None:
    """EN-09: Important opaque actions should expose a stable target."""
    if not _is_true(page.get("important_action")):
        return None

    if not _is_true(page.get("opaque_interaction")):
        return None

    if _text(page.get("direct_target")):
        return None

    return _finding(
        "EN-09",
        "Important action lacks a stable direct target",
        (
            "An important action is explicitly marked as depending on "
            "an opaque interaction, but no direct target URL was extracted."
        ),
        "medium",
    )


def check_content_action_consistency(
    page: dict[str, Any],
) -> dict[str, str] | None:
    """EN-10: Page promise must materially match destination purpose."""
    if not _is_true(page.get("action_mismatch")):
        return None

    page_promise = _text(page.get("page_promise"))
    destination_purpose = _text(page.get("destination_purpose"))

    # A mismatch flag without the evidence needed to explain it should
    # not produce a finding.
    if not page_promise or not destination_purpose:
        return None

    return _finding(
        "EN-10",
        "Page promise and action destination are inconsistent",
        (
            f"Page promise is '{page_promise}', while destination "
            f"purpose is '{destination_purpose}'."
        ),
        "high",
    )


def check_action_context(page: dict[str, Any]) -> dict[str, str] | None:
    """EN-11: Important actions need meaningful textual context."""
    actions = page.get("actions") or []

    visual_only = [
        action
        for action in actions
        if isinstance(action, dict)
        and _is_true(action.get("important"))
        and _is_true(action.get("visual_only"))
        and not _text(action.get("text_context"))
    ]

    if not visual_only:
        return None

    return _finding(
        "EN-11",
        "Important action lacks textual context",
        (
            f"{len(visual_only)} important action(s) were deterministically "
            "identified as visual/interaction-dependent without equivalent "
            "textual context."
        ),
        "medium",
    )


def check_conversion_path(page: dict[str, Any]) -> dict[str, str] | None:
    """EN-12: Explicitly defined journeys must contain required steps."""
    if not _is_true(page.get("conversion_path")):
        return None

    required = page.get("required_steps") or []
    available = page.get("available_steps") or []

    if not isinstance(required, (list, tuple, set)):
        return None

    if not isinstance(available, (list, tuple, set)):
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
        "Conversion path is missing a required step",
        (
            "Required journey steps not represented in the available "
            f"path: {', '.join(map(str, missing))}."
        ),
        "high",
    )


def run_checks(page: dict[str, Any]) -> list[dict[str, str]]:
    """Run all Engagement Audit checks."""
    results: list[dict[str, str]] = []

    results.extend(check_cta_targets(page))
    results.extend(check_cta_clarity(page))
    results.extend(check_form_actionability(page))

    single_checks = (
        check_primary_cta,
        check_value_proposition,
        check_decision_information,
        check_contact_action_path,
        check_follow_up_path,
        check_stable_direct_url,
        check_content_action_consistency,
        check_action_context,
        check_conversion_path,
    )

    for check in single_checks:
        result = check(page)
        if result is not None:
            results.append(result)

    return results


if __name__ == "__main__":
    import json
    import sys

    payload = json.load(sys.stdin)
    print(json.dumps(run_checks(payload), indent=2))
