from __future__ import annotations

from typing import Any, Mapping


SOURCE = "engagement-audit"
CATEGORY = "engagement"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _items(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _dict_items(value: Any) -> list[dict[str, Any]]:
    return [
        item
        for item in _items(value)
        if isinstance(item, dict)
    ]


def _finding(
    page: Mapping[str, Any],
    check_id: str,
    title: str,
    evidence: str,
    severity: str,
    why_it_matters: str,
    action_summary: str,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "source_skill": SOURCE,
        "url": _text(page.get("final_url") or page.get("url")),
        "category": CATEGORY,
        "title": title,
        "severity": severity,
        "evidence": evidence,
        "why_it_matters": why_it_matters,
        "suggested_action": {
            "summary": action_summary,
            "priority": severity,
        },
    }


def _links(page: Mapping[str, Any]) -> list[dict[str, Any]]:
    return _dict_items(page.get("links"))


def _buttons(page: Mapping[str, Any]) -> list[dict[str, Any]]:
    return _dict_items(page.get("buttons"))


def _forms(page: Mapping[str, Any]) -> list[dict[str, Any]]:
    return _dict_items(page.get("forms"))


def _label(item: Mapping[str, Any]) -> str:
    return _text(
        item.get("text")
        or item.get("aria_label")
        or item.get("title")
    )


def _has_action_evidence(page: Mapping[str, Any]) -> bool:
    return bool(
        _links(page)
        or _buttons(page)
        or _forms(page)
    )


def _has_label(item: Mapping[str, Any]) -> bool:
    return bool(_label(item))


def _has_page_description(page: Mapping[str, Any]) -> bool:
    if _text(page.get("title")):
        return True

    if _text(page.get("meta_description")):
        return True

    for field in ("h1", "h2"):
        for heading in _items(page.get(field)):
            if _text(heading):
                return True

    return False


def _is_empty_href(value: Any) -> bool:
    href = _text(value)

    if not href:
        return True

    return href in {"#", "#!"}


def _is_true(value: Any) -> bool:
    return value is True


def check_primary_cta(
    page: Mapping[str, Any],
) -> dict[str, Any] | None:
    """
    EN-01.

    PageResult does not establish page intent or identify a primary CTA.
    Therefore this check only reports a complete absence of extracted
    action evidence.
    """

    if _has_action_evidence(page):
        return None

    return _finding(
        page,
        "EN-01",
        "No actionable element was extracted",
        (
            "The engagement adapter extracted no links, buttons, or forms "
            "from the supplied page evidence."
        ),
        "medium",
        (
            "No directly observable action mechanism is available in the "
            "supplied evidence."
        ),
        (
            "Expose an appropriate actionable element when the page is "
            "intended to support a user journey."
        ),
    )


def check_cta_targets(
    page: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """
    EN-02.

    PageResult does not contain per-target HTTP response statuses.
    Therefore this check does not claim that a target returned 4xx/5xx.

    It only reports directly observable empty or fragment-only hrefs.
    """

    findings: list[dict[str, Any]] = []

    for index, link in enumerate(_links(page), start=1):
        href = _text(link.get("href"))

        if not _is_empty_href(href):
            continue

        label = _label(link) or "(unlabelled link)"

        findings.append(
            _finding(
                page,
                f"EN-02-{index}",
                "Action link has no usable target",
                (
                    f"Link '{label}' has an empty or fragment-only href "
                    f"('{href or '(empty)'}')."
                ),
                "high",
                (
                    "The extracted link does not expose a concrete "
                    "destination for the action."
                ),
                (
                    "Provide a valid destination or represent the control "
                    "as an appropriate non-link interaction."
                ),
            )
        )

    return findings


def check_cta_clarity(
    page: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """
    EN-03.

    Current evidence can establish whether an extracted link or button has
    textual/accessibility labelling. It cannot establish semantic mismatch
    with a destination because target-page purpose is not available.
    """

    findings: list[dict[str, Any]] = []

    for index, link in enumerate(_links(page), start=1):
        if _has_label(link):
            continue

        href = _text(link.get("href"))

        findings.append(
            _finding(
                page,
                f"EN-03-LINK-{index}",
                "Link has no extracted textual label",
                (
                    f"Link targeting '{href or '(empty)'}' has no extracted "
                    "text, aria-label, or title."
                ),
                "medium",
                (
                    "The supplied evidence does not expose a textual or "
                    "accessible label for the link."
                ),
                (
                    "Provide meaningful link text or an equivalent "
                    "accessible name."
                ),
            )
        )

    for index, button in enumerate(_buttons(page), start=1):
        if _has_label(button):
            continue

        findings.append(
            _finding(
                page,
                f"EN-03-BUTTON-{index}",
                "Button has no extracted textual label",
                (
                    "An extracted button has no text, aria-label, or title "
                    "in the supplied evidence."
                ),
                "medium",
                (
                    "The supplied evidence does not expose a textual or "
                    "accessible label for the button."
                ),
                (
                    "Provide meaningful button text or an equivalent "
                    "accessible name."
                ),
            )
        )

    return findings


def check_value_proposition(
    page: Mapping[str, Any],
) -> dict[str, Any] | None:
    """
    EN-04.

    PageResult provides title, meta description, H1 and H2 evidence but
    does not provide a semantic value_proposition field. This check therefore
    evaluates only whether any direct page-level descriptive evidence exists.
    """

    if _has_page_description(page):
        return None

    return _finding(
        page,
        "EN-04",
        "No page-level descriptive content was extracted",
        (
            "The supplied PageResult contains no title, meta description, "
            "H1, or H2 text."
        ),
        "medium",
        (
            "The supplied evidence does not expose direct textual context "
            "describing the page subject or offering."
        ),
        (
            "Expose clear page-level descriptive content through the title, "
            "meta description, or visible headings."
        ),
    )


def check_decision_information(
    page: Mapping[str, Any],
) -> dict[str, Any] | None:
    """
    EN-05.

    The current PageResult and engagement adapter do not establish required
    decision facts. The check therefore remains evidence-gated.
    """

    required = [
        _text(item)
        for item in _items(page.get("required_facts"))
        if _text(item)
    ]

    missing = [
        _text(item)
        for item in _items(page.get("missing_facts"))
        if _text(item)
    ]

    if not required or not missing:
        return None

    missing_required = sorted(
        set(required) & set(missing)
    )

    if not missing_required:
        return None

    return _finding(
        page,
        "EN-05",
        "Required decision information is missing",
        (
            "Explicitly supplied required decision facts not represented: "
            + ", ".join(missing_required)
            + "."
        ),
        "medium",
        (
            "A decision fact explicitly established as necessary is absent "
            "from the supplied evidence."
        ),
        (
            "Expose the missing decision information or provide a direct "
            "path to it."
        ),
    )


def check_contact_action_path(
    page: Mapping[str, Any],
) -> dict[str, Any] | None:
    """
    EN-06.

    PageResult does not classify intent or establish a required journey
    action. This check fires only when an upstream evidence producer
    explicitly supplies expected_action_path.
    """

    expected = _text(page.get("expected_action_path"))

    if not expected:
        return None

    action_path = _text(page.get("action_path"))

    if action_path:
        return None

    return _finding(
        page,
        "EN-06",
        "Explicitly required action path is absent",
        (
            f"The supplied evidence explicitly requires action path "
            f"'{expected}', but no action path was supplied."
        ),
        "high",
        (
            "An explicitly established journey requirement has no "
            "corresponding action route."
        ),
        (
            "Expose the required action route and verify that it is "
            "represented in the page evidence."
        ),
    )


def check_form_actionability(
    page: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """
    EN-07.

    The adapter directly provides form action, method, controls and
    has_submit. Therefore the only unconditional form defect currently
    supported is absence of an extracted submit control.
    """

    findings: list[dict[str, Any]] = []

    for index, form in enumerate(_forms(page), start=1):
        if form.get("has_submit") is True:
            continue

        controls = _dict_items(form.get("controls"))

        findings.append(
            _finding(
                page,
                f"EN-07-{index}",
                "Form has no extracted submit control",
                (
                    f"Form {index} contains {len(controls)} extracted "
                    "control(s), but no submit control was detected."
                ),
                "medium",
                (
                    "The supplied HTML evidence does not expose a standard "
                    "control for submitting the form."
                ),
                (
                    "Provide an explicit submit control appropriate to "
                    "the form's intended action."
                ),
            )
        )

    return findings


def check_follow_up_path(
    page: Mapping[str, Any],
) -> dict[str, Any] | None:
    """
    EN-08.

    Follow-up requirements are not established by PageResult, so this
    check remains inactive unless upstream evidence explicitly supplies
    follow_up_expected=True.
    """

    if not _is_true(page.get("follow_up_expected")):
        return None

    links = _items(page.get("follow_up_links"))

    if links:
        return None

    return _finding(
        page,
        "EN-08",
        "Required follow-up path is absent",
        (
            "The supplied evidence explicitly establishes that follow-up "
            "information is required, but no follow-up path was supplied."
        ),
        "medium",
        (
            "An explicitly established follow-up requirement has no "
            "corresponding information path."
        ),
        (
            "Provide the required follow-up information or a direct "
            "path to it."
        ),
    )


def check_stable_direct_url(
    page: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """
    EN-09.

    Opaque interaction is not inferable from ordinary HTML. This check only
    fires when opaque_interaction=True is explicitly supplied upstream.
    """

    findings: list[dict[str, Any]] = []

    for index, link in enumerate(_links(page), start=1):
        if link.get("opaque_interaction") is not True:
            continue

        href = _text(link.get("href"))

        if href and not _is_empty_href(href):
            continue

        label = _label(link) or "(unlabelled link)"

        findings.append(
            _finding(
                page,
                f"EN-09-{index}",
                "Important opaque action lacks a stable direct target",
                (
                    f"Action '{label}' is explicitly marked opaque but "
                    "has no usable direct href."
                ),
                "medium",
                (
                    "The explicitly identified opaque action has no stable "
                    "directly addressable representation."
                ),
                (
                    "Expose a stable direct URL or equivalent "
                    "machine-readable representation."
                ),
            )
        )

    return findings


def check_content_action_consistency(
    page: Mapping[str, Any],
) -> dict[str, Any] | None:
    """
    EN-10.

    Destination purpose cannot be inferred from href alone. The check fires
    only when an upstream evidence producer explicitly establishes a mismatch.
    """

    if page.get("action_mismatch") is not True:
        return None

    promise = _text(page.get("page_promise"))
    destination = _text(page.get("destination_purpose"))

    if not promise or not destination:
        return None

    return _finding(
        page,
        "EN-10",
        "Page promise and action destination are inconsistent",
        (
            f"Page promise: '{promise}'. "
            f"Destination purpose: '{destination}'. "
            "The supplied evidence explicitly marks them inconsistent."
        ),
        "high",
        (
            "The explicitly established page promise does not align with "
            "the explicitly established action destination."
        ),
        (
            "Align the page promise and the destination/action purpose."
        ),
    )


def check_action_context(
    page: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """
    EN-11.

    Current adapter evidence supports labels from visible text, aria-label
    and title. Important-action classification is not produced by the
    adapter, so this check only operates when important=True is explicitly
    supplied.
    """

    findings: list[dict[str, Any]] = []

    for index, link in enumerate(_links(page), start=1):
        if link.get("important") is not True:
            continue

        if _has_label(link):
            continue

        href = _text(link.get("href"))

        findings.append(
            _finding(
                page,
                f"EN-11-LINK-{index}",
                "Important link lacks textual action context",
                (
                    f"Important link targeting '{href or '(empty)'}' has "
                    "no extracted text, aria-label, or title."
                ),
                "medium",
                (
                    "The supplied evidence does not expose textual context "
                    "for the explicitly important action."
                ),
                (
                    "Provide meaningful link text or an equivalent "
                    "machine-readable accessible name."
                ),
            )
        )

    for index, button in enumerate(_buttons(page), start=1):
        if button.get("important") is not True:
            continue

        if _has_label(button):
            continue

        findings.append(
            _finding(
                page,
                f"EN-11-BUTTON-{index}",
                "Important button lacks textual action context",
                (
                    "An explicitly important button has no extracted text, "
                    "aria-label, or title."
                ),
                "medium",
                (
                    "The supplied evidence does not expose textual context "
                    "for the explicitly important action."
                ),
                (
                    "Provide meaningful button text or an equivalent "
                    "machine-readable accessible name."
                ),
            )
        )

    return findings


def check_conversion_path(
    page: Mapping[str, Any],
) -> dict[str, Any] | None:
    """
    EN-12.

    Journey steps are not supplied by the current PageResult adapter.
    Therefore this check activates only when required_steps and
    available_steps are explicitly supplied upstream.
    """

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

    missing = [
        step
        for step in required
        if step not in available
    ]

    if not missing:
        return None

    return _finding(
        page,
        "EN-12",
        "Explicit conversion path is missing a required step",
        (
            "Required journey steps not represented: "
            + ", ".join(missing)
            + "."
        ),
        "high",
        (
            "An explicitly established journey requirement is not "
            "represented in the supplied evidence."
        ),
        (
            "Expose the missing journey step and verify the complete "
            "journey representation."
        ),
    )


def run_checks(
    page: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """
    Run EN-01 through EN-12 against normalized engagement evidence.
    """

    results: list[dict[str, Any]] = []

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

    payload = json.load(sys.stdin)

    print(
        json.dumps(
            run_checks(payload),
            indent=2,
        )
    )
