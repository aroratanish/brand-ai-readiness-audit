from __future__ import annotations

from typing import Any, Mapping


SOURCE = "engagement-audit"
CATEGORY = "engagement"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _items(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


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
        "url": _text(
            page.get("final_url")
            or page.get("url")
        ),
        "category": CATEGORY,
        "title": title,
        "severity": severity,
        "evidence": evidence,
        "why_it_matters": why_it_matters,
        "suggested_action": suggested_action,
    }


def _action_label(item: Mapping[str, Any]) -> str:
    return _text(
        item.get("text")
        or item.get("aria_label")
        or item.get("title")
    )


def check_link_labels(
    page: Mapping[str, Any],
) -> list[dict[str, str]]:
    findings = []

    for link in _items(page.get("links")):
        if not isinstance(link, dict):
            continue

        href = _text(link.get("href"))

        if not href:
            continue

        if _action_label(link):
            continue

        findings.append(
            _finding(
                page,
                "EN-01",
                "Link lacks a discernible text label",
                (
                    f"Link target '{href}' has no visible text, "
                    "ARIA label, or title in the extracted HTML."
                ),
                "medium",
                (
                    "An unlabeled link is harder for users and "
                    "machine-readable interfaces to identify."
                ),
                (
                    "Provide a concise visible label or an equivalent "
                    "accessible name for the link."
                ),
            )
        )

    return findings


def check_button_labels(
    page: Mapping[str, Any],
) -> list[dict[str, str]]:
    findings = []

    for button in _items(page.get("buttons")):
        if not isinstance(button, dict):
            continue

        if _action_label(button):
            continue

        findings.append(
            _finding(
                page,
                "EN-02",
                "Button lacks a discernible label",
                (
                    "A button was extracted without visible text, "
                    "ARIA label, or title."
                ),
                "medium",
                (
                    "Users and machine-readable interfaces may not be "
                    "able to determine what the control does."
                ),
                (
                    "Give the button a concise visible label or "
                    "equivalent accessible name."
                ),
            )
        )

    return findings


def check_form_submission(
    page: Mapping[str, Any],
) -> list[dict[str, str]]:
    findings = []

    for form in _items(page.get("forms")):
        if not isinstance(form, dict):
            continue

        if form.get("has_submit") is True:
            continue

        findings.append(
            _finding(
                page,
                "EN-03",
                "Form has no explicit submit control",
                (
                    "A form was extracted, but no submit button or "
                    "submit input was found in the rendered/raw HTML."
                ),
                "medium",
                (
                    "The extracted form does not expose an explicit "
                    "submission control."
                ),
                (
                    "Provide an explicit submit control where the form "
                    "requires user submission."
                ),
            )
        )

    return findings


def check_empty_action_targets(
    page: Mapping[str, Any],
) -> list[dict[str, str]]:
    findings = []

    for link in _items(page.get("links")):
        if not isinstance(link, dict):
            continue

        href = _text(link.get("href"))

        if href:
            continue

        label = _action_label(link)

        if not label:
            continue

        findings.append(
            _finding(
                page,
                "EN-04",
                "Labeled link has no href target",
                (
                    f"Link labeled '{label}' was extracted without "
                    "an href target."
                ),
                "medium",
                (
                    "A labeled navigation/action element without a "
                    "target may not provide a usable destination."
                ),
                (
                    "Provide a valid destination or use an appropriate "
                    "interactive control."
                ),
            )
        )

    return findings


def check_empty_forms(
    page: Mapping[str, Any],
) -> list[dict[str, str]]:
    findings = []

    for form in _items(page.get("forms")):
        if not isinstance(form, dict):
            continue

        controls = _items(form.get("controls"))

        if controls:
            continue

        findings.append(
            _finding(
                page,
                "EN-05",
                "Form contains no extracted controls",
                (
                    "A form element was found, but no input, select, "
                    "textarea, or button controls were extracted."
                ),
                "low",
                (
                    "An empty form provides no directly observable "
                    "interaction path."
                ),
                (
                    "Add the required form controls or remove the "
                    "unused form element."
                ),
            )
        )

    return findings


def check_page_actionability(
    page: Mapping[str, Any],
) -> dict[str, str] | None:
    links = [
        item
        for item in _items(page.get("links"))
        if isinstance(item, dict)
        and _text(item.get("href"))
    ]

    buttons = [
        item
        for item in _items(page.get("buttons"))
        if isinstance(item, dict)
    ]

    forms = [
        item
        for item in _items(page.get("forms"))
        if isinstance(item, dict)
    ]

    if links or buttons or forms:
        return None

    return _finding(
        page,
        "EN-06",
        "No actionable HTML elements were extracted",
        (
            "No links with href targets, buttons, or forms were found "
            "in the selected HTML representation."
        ),
        "low",
        (
            "The page exposes no directly observable HTML interaction "
            "or navigation elements."
        ),
        (
            "If the page is intended to support navigation or an action, "
            "expose the relevant action through standard HTML controls."
        ),
    )


def check_internal_navigation(
    page: Mapping[str, Any],
) -> dict[str, str] | None:
    internal_links = [
        _text(item)
        for item in _items(page.get("internal_links"))
        if _text(item)
    ]

    if internal_links:
        return None

    return _finding(
        page,
        "EN-07",
        "No internal navigation links were extracted",
        (
            "PageResult contains an empty internal_links collection."
        ),
        "low",
        (
            "The page has no observed internal navigation targets "
            "in the crawler's extracted link set."
        ),
        (
            "Provide relevant internal navigation where the page "
            "requires onward discovery."
        ),
    )


def check_external_link_context(
    page: Mapping[str, Any],
) -> dict[str, str] | None:
    external_links = [
        _text(item)
        for item in _items(page.get("external_links"))
        if _text(item)
    ]

    if external_links:
        return None

    return None


def run_checks(
    page: Mapping[str, Any],
) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []

    checks = (
        check_link_labels,
        check_button_labels,
        check_form_submission,
        check_empty_action_targets,
        check_empty_forms,
        check_page_actionability,
        check_internal_navigation,
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
