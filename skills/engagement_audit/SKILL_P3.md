---
name: engagement-audit
description: Audit whether important customer-facing website journeys provide clear, reachable, understandable, and actionable next steps using deterministic evidence.
license: your-choice
---

# Engagement Audit

## Purpose

Assess whether important customer journeys provide a clear, reachable, understandable, and actionable path from user intent to the appropriate next action.

The skill evaluates concrete engagement and actionability signals. It does not make subjective visual or UX-quality judgments.

## Inputs

The P3 adapter must normalize the repository's real `PageResult` into observable evidence.

Supported logical inputs include:

- `url`: audited page URL.
- `intent`: deterministically established page/journey intent.
- `high_intent`: explicit high-intent signal when available.
- `core_service`: explicit core-service signal when available.
- `ctas`: extracted actions containing label/text, target, importance, and status when available.
- `required_facts`: decision facts established as necessary for the journey.
- `missing_facts`: required facts demonstrably absent from inspected evidence.
- `value_proposition`: directly extracted offering/audience/use context.
- `contact_path`: discoverable contact route.
- `booking_path`: discoverable booking route.
- `purchase_path`: discoverable purchase route.
- `demo_path`: discoverable demo route.
- `application_path`: discoverable application route.
- `support_path`: discoverable support route.
- `follow_up_expected`: explicit indication that follow-up information is required.
- `follow_up_links`: relevant FAQ/help/docs/support paths.
- `forms`: important forms with observable purpose and submission signals.
- `actions`: important interactions and their textual/machine-readable context.
- `page_promise`: directly established page promise.
- `destination_purpose`: directly established destination/action purpose.
- `action_mismatch`: deterministic material mismatch signal.
- `required_steps`: explicitly established journey steps.
- `available_steps`: journey steps represented by the inspected evidence.

The adapter must provide observed evidence only.

Do not manufacture intent, importance, required facts, missing information, or journey steps.

## Procedure

1. Establish page or journey intent from deterministic evidence.
2. Determine whether the journey is high-intent or core-service when supported.
3. Identify the appropriate expected action.
4. Inspect observable CTA, action, destination, content, form, and decision-information signals.
5. Preserve `UNKNOWN` when required evidence cannot be established.
6. Trigger only checks supported by deterministic evidence.
7. Convert triggered checks into the repository's canonical `Finding` structure.
8. Return findings to the orchestrator.
9. Do not perform orchestration or cross-skill deduplication.

## Deterministic Checks

### EN-01 — Primary CTA / Next Action Presence

Flag only when a deterministically high-intent page has no identifiable actionable CTA or equivalent appropriate action route.

Do not flag informational pages solely because they lack a CTA.

### EN-02 — CTA Reachability

Flag only when an important CTA target is demonstrably unreachable, such as an observed 4xx/5xx response.

If target status cannot be established, treat it as `UNKNOWN`.

If generic crawler/link checking already owns the failure, report the engagement consequence only when it is distinct.

### EN-03 — CTA Clarity

Flag only when deterministic evidence establishes a material CTA ambiguity or a mismatch between CTA wording and destination purpose.

Do not make subjective judgments about wording.

### EN-04 — Value Proposition Clarity

Use directly extracted page content such as title, headings, metadata, and relevant text.

Flag only when the normalized evidence demonstrates that the offering, intended audience, or use context is not adequately identifiable.

Do not infer absence merely because one extraction field is empty.

### EN-05 — Decision Information

Evaluate only facts established as necessary for the identified journey.

Flag only when those required facts are demonstrably absent from the inspected evidence.

Failure to extract a fact is not automatically proof that the fact is absent.

### EN-06 — Contact / Action Path

Flag only when the page is deterministically established as a core-service journey and no appropriate action route is found.

The expected action must match the established intent, such as:

- purchase;
- booking;
- contact;
- demo;
- application;
- support.

### EN-07 — Form Actionability

Evaluate only forms identified as important.

Flag when deterministic evidence shows a missing clear purpose, submit control, required submission target, or usable submission path.

Do not require a target or other form signal unless the identified journey requires it.

### EN-08 — Follow-up Path

Flag only when the journey demonstrably requires additional follow-up information and no relevant FAQ, help, documentation, support, or equivalent path is found.

Do not require such links on every page.

### EN-09 — Stable Direct URL

Flag only when an important action is explicitly interaction-dependent or opaque and has no usable direct target or equivalent direct representation.

Do not flag ordinary buttons merely because they do not expose a URL.

### EN-10 — Content / Action Consistency

Flag only when the page promise materially conflicts with the destination or action purpose.

Minor wording differences are insufficient.

### EN-11 — AI-Readable Action Context

Flag only when an important action is demonstrably dependent on visual or interaction context and lacks meaningful textual, accessibility, or machine-readable representation.

### EN-12 — Conversion-Path Completeness

Evaluate only explicitly established customer journeys.

Flag when one or more explicitly required journey steps are missing from the available evidence.

Do not invent required steps.

## Finding Contract

Every emitted finding must conform to the repository's canonical `Finding` structure:

- `id`
- `source_skill`
- `url`
- `category`
- `title`
- `severity`
- `evidence`
- `why_it_matters`
- `suggested_action`

For Engagement Audit:

- `source_skill = "engagement-audit"`
- `category = "engagement"`

Evidence must identify:

1. the observed page or action;
2. the deterministic condition that triggered the check;
3. relevant labels, URLs, status codes, or missing required facts where available.

Each finding must be reproducible by another auditor using the supplied evidence.

## Severity

Use the lowest severity justified by the evidence.

- `critical` — severe, demonstrably blocked core action.
- `high` — major core-journey failure or materially misleading action.
- `medium` — meaningful actionability or decision-information issue.
- `low` — minor issue with limited impact.

Do not escalate severity without supporting evidence.

## Output Rules

For every triggered check, provide:

1. the exact page or action inspected;
2. the deterministic result;
3. the supporting evidence;
4. the customer/AI engagement impact;
5. a concrete prioritized remediation.

Do not use subjective labels such as `bad UX`, `ugly`, or `confusing` unless a deterministic signal supports the conclusion.

When required evidence is unavailable, do not trigger the check. Treat the evidence state as `UNKNOWN`, not as absence or failure.

## Ownership Boundaries

Engagement Audit does not own:

- crawling mechanics;
- generic HTTP/link checking;
- robots.txt compliance;
- canonical/meta/JSON-LD validation;
- marketplace registration;
- orchestration;
- cross-skill deduplication;
- proprietary search or ranking algorithms.

A raw HTTP failure normally remains a crawler/technical finding. P3 may additionally report its distinct customer-action consequence when that consequence is supported by evidence.

## References and Implementation

Use the accompanying `references/` files for the check catalogue and research rationale.

Use `scripts/engagement_checks.py` for dependency-free deterministic check helpers.

The P3 adapter/orchestrator is responsible for mapping the repository's actual `PageResult` into the logical inputs defined above.

The checker must not crawl pages, invent evidence, perform orchestration, or deduplicate findings.

## Quality Gate

A valid Engagement Audit finding must follow:

PageResult → P3 normalization → EN check → canonical Finding

Every finding must be:

- deterministic;
- reproducible;
- evidence-backed;
- attributable to one EN check;
- within P3 ownership.

If the required evidence cannot be established, the check must not produce a finding.
