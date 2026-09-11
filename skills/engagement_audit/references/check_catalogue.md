# Engagement Audit — P3 Check Catalogue

## Purpose

Assess whether important customer journeys have a clear, reachable, understandable, and actionable path from intent to the appropriate next action.

## Evidence Rules

- Use only observable `PageResult` or site evidence.
- `UNKNOWN` is not the same as absent or failed.
- Never fabricate evidence.
- Apply high-intent or core-service checks only when intent is deterministically established.
- Every finding must be reproducible and traceable to source evidence.
- A missing extraction value alone does not prove that information is absent.

## Check Catalogue

| ID | Check | Trigger | Severity |
|---|---|---|---|
| EN-01 | Primary CTA / Next Action Presence | High-intent page has no identifiable actionable CTA or equivalent appropriate action route. | Medium |
| EN-02 | CTA Reachability | Important CTA target is demonstrably unreachable, such as an observed 4xx/5xx response. | High |
| EN-03 | CTA Clarity | CTA wording is deterministically and materially ambiguous or conflicts with destination purpose. | High |
| EN-04 | Value Proposition Clarity | High-intent page lacks adequately observable offering, audience, or use context. | Medium |
| EN-05 | Decision Information | A fact established as necessary for the identified journey is demonstrably absent from inspected evidence. | Medium |
| EN-06 | Contact / Action Path | Core-service journey has no appropriate discoverable route to its expected action. | High |
| EN-07 | Form Actionability | Important form lacks a required purpose, submit control, required submission target, or usable submission path. | Medium |
| EN-08 | Follow-up Path | Journey requires follow-up information but no relevant FAQ, help, documentation, support, or equivalent path is found. | Medium |
| EN-09 | Stable Direct URL | Important opaque or interaction-dependent action has no usable direct target or equivalent direct representation. | Medium |
| EN-10 | Content / Action Consistency | Page promise materially conflicts with the destination or action purpose. | High |
| EN-11 | AI-Readable Action Context | Important interaction-dependent action lacks meaningful textual, accessibility, or machine-readable context. | Medium |
| EN-12 | Conversion-Path Completeness | Explicitly established journey is missing one or more required steps. | High |

## Check Rules

### EN-01 — Primary CTA / Next Action Presence

Flag only when a deterministically high-intent page has no identifiable actionable CTA or equivalent appropriate action route.

Do not flag ordinary informational pages solely because they lack a CTA.

### EN-02 — CTA Reachability

Flag only when an important CTA target is demonstrably unreachable.

If target status cannot be established, treat it as `UNKNOWN`.

### EN-03 — CTA Clarity

Flag only when deterministic evidence establishes a material CTA ambiguity or mismatch between CTA wording and destination purpose.

Do not make subjective judgments about wording.

### EN-04 — Value Proposition Clarity

Use directly extracted content such as title, H1, H2, metadata, and relevant text.

Do not infer missing information merely because one normalized extraction field is empty.

### EN-05 — Decision Information

Evaluate only facts established as necessary for the identified journey.

A failed extraction does not automatically prove that a fact is absent.

### EN-06 — Contact / Action Path

Flag only for a deterministically established core-service journey with no appropriate route to the expected action.

The expected action must match the page intent, such as purchase, booking, contact, demo, application, or support.

### EN-07 — Form Actionability

Evaluate only important forms.

Flag when deterministic evidence shows a missing clear purpose, submit control, required submission target, or usable submission path.

Do not require a target or other form signal unless the journey requires it.

### EN-08 — Follow-up Path

Require a follow-up path only when the journey demonstrably needs additional information.

Do not require FAQ, help, documentation, or support links on every page.

### EN-09 — Stable Direct URL

Flag only important actions that explicitly depend on an opaque interaction and have no usable direct target or equivalent direct representation.

Do not flag ordinary buttons merely because they do not expose a URL.

### EN-10 — Content / Action Consistency

Flag only when the page promise materially conflicts with the destination or action purpose.

Minor wording differences are insufficient.

### EN-11 — AI-Readable Action Context

Flag only when an important action is demonstrably dependent on visual or interaction context and lacks meaningful textual, accessibility, or machine-readable representation.

### EN-12 — Conversion-Path Completeness

Evaluate only explicitly established customer journeys.

Do not invent required journey steps.

## Finding Output

Each triggered check must be converted to the repository's canonical `Finding` structure.

Required fields:

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

Evidence must identify the observed page or action and the specific deterministic fact that triggered the check.

## Severity

Use the lowest severity supported by the evidence.

- **Critical:** severe, demonstrably blocked core action.
- **High:** major core-journey failure or materially misleading action.
- **Medium:** meaningful actionability or decision-information issue.
- **Low:** minor issue with limited impact.

## Boundaries

Engagement Audit does not own:

- crawling mechanics;
- generic broken-link detection;
- robots.txt compliance;
- metadata or JSON-LD validation;
- marketplace registration;
- orchestration;
- cross-skill deduplication;
- proprietary search or ranking algorithms.

## Quality Gate

A valid Engagement Audit finding must follow:

`PageResult → P3 normalization → EN check → canonical Finding`

Every finding must be deterministic, reproducible, evidence-backed, and attributable to a specific EN check.

When required evidence is unavailable, the check must not trigger. Treat the underlying evidence state as `UNKNOWN`, not as absence or failure.
