---
name: engagement-audit
description: Audit whether important customer-facing website journeys provide a clear, reachable, understandable and actionable path from user intent to the appropriate next action. Use deterministic evidence and preserve UNKNOWN rather than inferring defects.
license: your-choice
---

# Engagement Audit

## Purpose

Audit the on-site engagement side of the Round-3 problem:

> Once a visitor or AI/search system reaches a website, can the relevant offering be understood, the information needed for a decision be found, and the appropriate next action be reached?

The audit is evidence-first. It detects concrete actionability, discoverability and journey-completion problems; it does not judge visual aesthetics or subjective UX preferences.

## When to use

Use this skill on normalized page/site evidence produced by the repository's crawler/render layer.

Do not use it for:

- generic crawl/link mechanics;
- robots.txt, canonical, metadata or JSON-LD syntax validation;
- freshness/corroboration;
- proprietary product/search ranking;
- orchestration or cross-skill deduplication.

## Inputs

The upstream adapter must normalize the repository's real `PageResult` into evidence-backed logical fields. Fields may be `UNKNOWN` when evidence cannot establish them.

### Page and intent

- `url`
- `page_type`
- `intent`
- `high_intent`
- `core_service`
- `intent_evidence`

`high_intent`, `core_service`, and similar classifications must be established upstream from observable evidence. A non-empty `intent` string alone is not sufficient.

### Actions

`ctas`: actions with, where available:

- `text`
- `target`
- `status`
- `important`
- `actionable`
- `target_purpose`
- `mismatch`

`actions`: important interactions with, where available:

- `text`
- `important`
- `visual_only`
- `text_context`
- `link_context`
- `accessibility_context`
- `structured_context`

Action mechanisms may be links, buttons, forms, mailto/tel links, JavaScript controls, modals, dynamic routes, external destinations, or equivalent machine-readable mechanisms.

### Offering and decision information

- `value_proposition`
- `offering_context`
- `required_facts`
- `observed_facts`
- `missing_facts`
- `evidence_for_requirement`

Required decision facts must be justified by the identified page/offering journey.

Do not assume that price, availability, reviews, or any other fact is universally required.

### Action routes

- `expected_action`
- `action_path`
- `contact_path`
- `booking_path`
- `purchase_path`
- `demo_path`
- `support_path`

The expected route must follow the established page/offer intent.

No particular CTA type is universally required.

### Forms and follow-up

`forms`: where available:

- `important`
- `purpose_clear`
- `submit_control`
- `requires_target`
- `target`
- `execution_result`

Also:

- `follow_up_expected`
- `follow_up_links`

Follow-up is required only where the journey establishes a genuine need for continuation or predictable follow-up information.

### Important/opaque actions

- `important_action`
- `opaque_interaction`
- `action_identifiable`
- `direct_target`

An ordinary button, modal, JavaScript action, dynamic route, or missing conventional URL is not itself a defect.

Opaqueness must materially prevent deterministic identification or invocation of an important action.

### Journey

- `page_promise`
- `destination_purpose`
- `action_mismatch`
- `conversion_path`
- `required_steps`
- `available_steps`
- `terminal_state`

Never invent a canonical conversion path.

Evaluate only explicitly established required steps.

## Procedure

1. Use only observable PageResult/site evidence.
2. Establish page type and journey intent from direct evidence.
3. Determine the context-appropriate expected action, if one is established.
4. Inspect actions, targets, offering information, decision facts, forms, follow-up paths, machine-readable context and journey steps.
5. Treat missing/unknown extraction as `UNKNOWN`, not as proof of absence.
6. Trigger only checks whose evidence preconditions are satisfied.
7. Produce concise, reproducible evidence identifying the inspected page/action and the deterministic observation.
8. Return check findings to the orchestrator/adapter for canonical Finding conversion, severity normalization and deduplication.

## Deterministic checks

### EN-01 — Primary CTA Presence

For a deterministically identified high-intent page, detect whether an actionable next step appropriate to the established intent is exposed.

Do not flag informational, editorial, documentation, legal, help or completed/confirmation pages merely because they lack a conversion CTA.

### EN-02 — CTA Reachability

For an important CTA whose target and observed status are available, trigger when the target is demonstrably unreachable, such as an observed HTTP 4xx/5xx response.

Do not convert an unavailable status into a failure.

Avoid duplicating a generic crawler finding unless the engagement consequence is distinct.

### EN-03 — CTA Clarity

Trigger only when CTA wording materially conflicts with the established destination purpose.

Short, unconventional or stylistically different wording is not sufficient evidence.

### EN-04 — Product/Service Information and Value Proposition

For a deterministically identified high-intent page, determine whether directly extracted content establishes the relevant offering and audience/use context needed to understand the page.

Do not require a particular marketing phrase.

Do not infer site-wide absence from one missing extraction field.

### EN-05 — Decision Information Completeness

For an established journey, evaluate only decision facts explicitly justified as necessary for that journey.

Trigger only when required facts are established and the evidence demonstrates that one or more are absent.

`UNKNOWN` or extraction failure is not proof of absence.

### EN-06 — Context-Appropriate Contact/Action Path

For a deterministically established core-service journey with a known expected action, detect whether an appropriate discoverable route exists, such as:

- purchase;
- booking;
- quote;
- sales contact;
- signup;
- demo;
- trial;
- application;
- support;
- contact;
- request-information.

Do not require a purchase CTA when the established intent calls for another action.

### EN-07 — Form Actionability

For an important form, trigger when the evidence demonstrates:

- a missing clear purpose;
- a missing usable submit control;
- a missing required submission target; or
- deterministic execution failure.

Do not require a target when the form architecture does not establish that one is needed.

### EN-08 — Required Follow-up Path

Trigger only when the established journey requires subsequent information/action and no relevant follow-up path is discovered.

Do not require FAQ/help/support on every page.

### EN-09 — Important Action Opaqueness

Trigger only when an important action is genuinely opaque:

- its destination or invocation cannot be deterministically established from available evidence;
- no usable direct target/representation exists; and
- the evidence explicitly establishes that the action is opaque.

Do not flag ordinary buttons, modals, JavaScript, dynamic routes or external flows merely because they are non-standard.

### EN-10 — Page/Action Consistency

Trigger when the established page promise materially conflicts with the purpose of the exposed action or resulting destination.

Minor wording differences are not sufficient.

### EN-11 — AI-Readable Action Context

For an important action, determine whether its purpose/destination can be established from meaningful:

- visible text;
- link context;
- accessibility metadata;
- structured information; or
- equivalent machine-readable evidence.

Trigger only when deterministic evidence shows that no meaningful textual or machine-readable representation exists.

### EN-12 — Conversion-Path Completeness

For an explicitly established journey, compare required steps with available/discovered steps.

Trigger only when one or more objectively required steps are absent or inaccessible.

Do not invent a canonical journey.

## Finding Contract

Each triggered check must ultimately become the repository's shared Finding:

- `id`
- `source_skill`: `engagement-audit`
- `url`
- `category`: `engagement`
- `title`
- `severity`: `critical`, `high`, `medium`, or `low`
- `evidence`
- `why_it_matters`
- `suggested_action`

`suggested_action` must contain a concise remediation and priority.

Evidence must identify:

1. the inspected page/action;
2. the deterministic observation;
3. the relevant label, URL, status or context where available;
4. why the check triggered.

The check script may return an intermediate check-level record only if the adapter/provider immediately converts it to the canonical Finding contract.

## Severity

- `critical` — core action is blocked or materially misleading with severe customer impact.
- `high` — major defect affects a core or broad customer journey.
- `medium` — meaningful actionability defect affects an important but narrower journey.
- `low` — minor optimization with limited impact.

Use the lowest severity justified by evidence.

Do not inflate severity.

## False-Positive Boundaries

- Missing extraction is not the same as proven absence.
- No internal link is not automatically a dead end.
- No conventional URL is not automatically a broken action.
- A modal or JavaScript action is not automatically opaque.
- `Talk to Sales` is not inherently a weak CTA.
- `Free Trial` instead of `Buy` is not inherently a mismatch.
- Price is not universally required.
- FAQ/help/support is not universally required.
- A page without a CTA is not automatically defective.
- An external payment, booking, authentication or application flow may be a valid continuation.
- Completed transactions, confirmations and successful submissions may legitimately terminate a journey.
- An unavailable field must not be interpreted as a negative observation.
- A classification must not be inferred solely from a free-text label.

## Ownership Boundaries

Engagement Audit does not own:

- robots.txt;
- HTTP crawling mechanics;
- generic broken-link detection;
- canonical/meta/JSON-LD syntax;
- marketplace registration;
- proprietary search/recommendation ranking;
- orchestration;
- cross-skill deduplication.

A raw HTTP failure normally remains a crawler/technical finding.

P3 may additionally report the distinct customer-action consequence when supported.

## Quality Gate

A valid Engagement finding must be traceable as:

`PageResult evidence → normalized P3 input → EN check → canonical Finding`

The audit must preserve uncertainty.

If the evidence cannot establish a defect, return no finding rather than inventing one.

The P3 Engagement layer is responsible for deterministic customer/actionability evidence, not for ranking products or deciding which products should appear in a search result.
