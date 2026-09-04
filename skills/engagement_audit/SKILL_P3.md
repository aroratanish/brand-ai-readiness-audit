---
name: engagement-audit
description: Audit whether important customer-facing website journeys provide clear, reachable, textually understandable next actions and the information needed to make decisions. Use deterministic evidence rather than subjective UX judgments.
license: your-choice
---

# Engagement Audit

## Purpose

Audit the on-site engagement half of the Round-2 problem: after a visitor or AI assistant reaches the site, can they understand the offering, find the information needed for a decision, and reach an appropriate next action?

The skill detects concrete actionability problems, not visual-design preferences.

## Inputs

The skill may receive normalized page/site data from the crawler. Adapt the repository's real `PageResult` fields to these logical inputs.

- `url`: audited page URL.
- `intent`: inferred or explicitly classified page intent when supported by deterministic content.
- `ctas`: extracted actions with textual label, target, and observed status when available.
- `required_facts`: decision facts relevant to the identified page intent.
- `missing_facts`: required facts that were not found.
- `actions`: important actions and whether equivalent textual context exists.
- `value_proposition`: directly extracted title/headings/summary information.
- `contact_path`, `booking_path`, `purchase_path`, `demo_path`, `support_path`: available action routes when extracted.
- `follow_up_links`: FAQ/help/docs/support or equivalent paths.
- `forms`: exposed labels, submit controls, and targets where available.

The adapter should provide observed evidence only. Do not manufacture intent or missing information when the page does not support the conclusion.

## Procedure

1. Establish the page's user/customer intent from direct content.
2. Identify the expected next action for that intent.
3. Inspect deterministic action, target, content, and decision-information signals.
4. Record exact URLs, labels, missing facts, and status codes where available.
5. Trigger only checks supported by evidence.
6. Convert each triggered check into the shared finding schema.
7. Return findings to the orchestrator; do not own orchestration or deduplication.

## Deterministic checks

### EN-01 — Primary CTA presence

For a clearly identifiable high-intent page, detect whether there is an identifiable useful next action.

Do not flag informational pages merely because they do not contain a conversion CTA.

### EN-02 — CTA reachability

Resolve an important CTA target when status information is available. Trigger when the core action target returns an error or is otherwise demonstrably unreachable.

If the repository's crawler already owns HTTP/link failures, emit this only when the finding is specifically about the customer action path and avoid duplicating the technical finding.

### EN-03 — CTA clarity

Compare CTA wording with its target purpose. Trigger only when the action is materially ambiguous or sends the user toward a purpose different from the one promised.

### EN-04 — Value proposition clarity

Use directly extracted title/headings/summary content to determine whether the offering and intended audience/use are reasonably identifiable. Trigger only where a concrete absence or contradiction is demonstrated.

### EN-05 — Decision information completeness

For an identifiable high-intent journey, detect important missing facts such as price, plan, scope, eligibility, location, availability, or equivalent decision criteria when those facts are necessary to the action.

### EN-06 — Contact/action path

Detect whether a core service has a discoverable route such as contact, booking, purchase, demo, application, or support. The expected route must follow the page's intent.

### EN-07 — Form actionability

Inspect exposed form labels, purpose, submit control, and action target. Trigger when an important form has a demonstrable lack of understandable purpose or usable submission path.

### EN-08 — Follow-up path

Check whether predictable follow-up questions have an available FAQ/help/docs/support path where the journey materially needs one.

### EN-09 — Stable direct URL

Check whether important information or actions have a usable direct target URL rather than depending entirely on an opaque interaction that cannot be represented textually.

### EN-10 — Content/action consistency

Compare the page's promise or heading with the destination/action. Trigger when the page promises one action but routes the visitor to an unrelated purpose.

### EN-11 — AI-readable action context

Check whether important actions have meaningful textual context. Trigger when the action is marked as visually dependent and no equivalent textual context is available.

### EN-12 — Conversion-path completeness

Trace the minimum path from intent → required decision information → action. Trigger when a concrete missing step prevents completion or leaves the visitor at a dead end.

## Finding contract

Every emitted finding must conform to the repository's shared finding schema:

- `id`
- `source_skill`: `engagement-audit`
- `url`
- `category`: `engagement`
- `title`
- `severity`: `critical`, `high`, `medium`, or `low`
- `evidence`
- `why_it_matters`
- `suggested_action` with a concise action summary and priority

Evidence must be concrete enough for another auditor to reproduce the finding.

## Severity

- **critical** — core action is blocked or materially misleading.
- **high** — major friction affects a broad or core journey.
- **medium** — actionable friction affects a narrower journey.
- **low** — minor optimization with limited impact.

Use the lower severity when evidence does not justify a stronger classification.

## Output rules

For each triggered check, emit:

1. the exact page/action inspected;
2. the deterministic result;
3. the evidence supporting the result;
4. the customer/AI engagement impact;
5. a concrete prioritized remediation.

Do not use subjective labels such as `bad UX`, `ugly`, or `confusing` without a deterministic supporting signal.

## Non-goals and ownership boundaries

Do not duplicate:

- robots.txt compliance;
- HTTP status/crawl mechanics;
- general broken-link crawling;
- canonical/meta/JSON-LD syntax checks;
- marketplace registration;
- orchestration;
- cross-skill deduplication.

A raw HTTP failure should normally remain a crawler/technical finding; this skill may additionally identify the customer-action consequence only when that consequence is distinct and supported.

## References and implementation

Use the accompanying `references/` files for the check catalogue and research rationale. Use `scripts/engagement_checks.py` for dependency-free deterministic helpers. The orchestrator should adapt real crawler output into the logical inputs above.
