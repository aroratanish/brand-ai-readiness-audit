"""Dependency-free deterministic engagement checks.

The crawler/orchestrator should adapt its real PageResult into the logical fields
listed in SKILL.md. These functions return check-level findings only.
"""
from __future__ import annotations

from urllib.parse import urljoin
from typing import Any


def _text(value: Any) -> str:
    return str(value or "").strip()


def _finding(check_id: str, title: str, evidence: str, severity: str) -> dict[str, str]:
    return {"check_id": check_id, "title": title, "evidence": evidence, "severity": severity}


def _has_cta(page: dict) -> bool:
    return any(isinstance(c, dict) and _text(c.get("text")) for c in (page.get("ctas") or []))


def check_primary_cta(page: dict) -> dict | None:
    if not page.get("high_intent") and not _text(page.get("intent")):
        return None
    if _has_cta(page):
        return None
    return _finding("EN-01", "No identifiable next action on a high-intent page",
                    f"Page intent is '{_text(page.get('intent'))}', but no actionable CTA was extracted.", "medium")


def check_cta_targets(page: dict) -> list[dict]:
    base = _text(page.get("url"))
    findings = []
    for cta in page.get("ctas") or []:
        if not isinstance(cta, dict) or cta.get("status") is None:
            continue
        try:
            status = int(cta.get("status"))
        except (TypeError, ValueError):
            continue
        if status >= 400:
            target = urljoin(base, _text(cta.get("target")))
            findings.append(_finding("EN-02", "Core action target is unreachable",
                                     f"CTA '{_text(cta.get('text'))}' targets {target} and returned HTTP {status}.", "high"))
    return findings


def check_cta_clarity(page: dict) -> list[dict]:
    findings = []
    for cta in page.get("ctas") or []:
        if not isinstance(cta, dict) or not cta.get("mismatch"):
            continue
        findings.append(_finding("EN-03", "CTA wording does not match its destination",
                                 f"CTA '{_text(cta.get('text'))}' is marked as materially mismatched with target purpose '{_text(cta.get('target_purpose'))}'.", "high"))
    return findings


def check_value_proposition(page: dict) -> dict | None:
    if not page.get("high_intent") or page.get("value_proposition"): 
        return None
    return _finding("EN-04", "Offering is not identifiable from direct page content",
                    "The page is marked high-intent, but no directly extracted value proposition was provided.", "medium")


def check_decision_information(page: dict) -> dict | None:
    missing = page.get("missing_facts") or []
    if not page.get("high_intent") or not missing:
        return None
    return _finding("EN-05", "Important decision information is missing",
                    f"Missing decision facts: {', '.join(map(str, missing))}.", "medium")


def check_contact_action_path(page: dict) -> dict | None:
    if not page.get("core_service") or page.get("action_path"):
        return None
    return _finding("EN-06", "Core service has no discoverable action path",
                    "The page is marked as a core service page, but no contact, booking, purchase, demo, application, or support route was extracted.", "high")


def check_form_actionability(page: dict) -> list[dict]:
    findings = []
    for form in page.get("forms") or []:
        if not isinstance(form, dict) or not form.get("important"):
            continue
        missing = []
        if not form.get("purpose_clear"):
            missing.append("clear purpose")
        if not form.get("submit_control"):
            missing.append("submit control")
        if form.get("requires_target") and not form.get("target"):
            missing.append("submission target")
        if missing:
            findings.append(_finding("EN-07", "Important form lacks an understandable action path",
                                     f"Missing form signals: {', '.join(missing)}.", "medium"))
    return findings


def check_follow_up_path(page: dict) -> dict | None:
    if not page.get("follow_up_expected") or page.get("follow_up_links"):
        return None
    return _finding("EN-08", "No useful follow-up information path was found",
                    "The journey is marked as requiring predictable follow-up information, but no FAQ/help/docs/support path was extracted.", "medium")


def check_stable_direct_url(page: dict) -> dict | None:
    if not page.get("important_action") or page.get("direct_target"):
        return None
    if not page.get("opaque_interaction"):
        return None
    return _finding("EN-09", "Important action lacks a stable direct target",
                    "An important action is marked as depending on an opaque interaction and no direct target URL was extracted.", "medium")


def check_content_action_consistency(page: dict) -> dict | None:
    if not page.get("action_mismatch"):
        return None
    return _finding("EN-10", "Page promise and action destination are inconsistent",
                    f"Page promise is '{_text(page.get('page_promise'))}', while destination purpose is '{_text(page.get('destination_purpose'))}'.", "high")


def check_action_context(page: dict) -> dict | None:
    actions = page.get("actions") or []
    visual_only = [a for a in actions if isinstance(a, dict) and a.get("visual_only")]
    if not visual_only:
        return None
    return _finding("EN-11", "Important action lacks textual context",
                    f"{len(visual_only)} important action(s) were marked visual-only with no equivalent textual context.", "medium")


def check_conversion_path(page: dict) -> dict | None:
    if not page.get("conversion_path"):
        return None
    missing = [step for step in (page.get("required_steps") or []) if step not in (page.get("available_steps") or [])]
    if not missing:
        return None
    return _finding("EN-12", "Conversion path is missing a required step",
                    f"Required journey steps not represented in the available path: {', '.join(map(str, missing))}.", "high")


def run_checks(page: dict) -> list[dict]:
    results: list[dict] = []
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
    print(json.dumps(run_checks(payload), indent=2))
