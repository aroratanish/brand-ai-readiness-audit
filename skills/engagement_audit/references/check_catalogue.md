# Engagement Audit — P3 Check Catalogue

## Purpose

Assess whether important customer journeys have a clear, reachable, understandable, and actionable path from intent to action.

## Evidence Rules

- Use only observable `PageResult` or site evidence.
- `UNKNOWN` is not the same as absent or failed. Never fabricate evidence.
- Apply high-intent or core-service checks only when page intent is deterministically established.
- Every finding must be reproducible and traceable to source evidence.

## Check Catalogue

| ID | Check | Trigger | Severity |
|---|---|---|---|
| EN-01 | Primary CTA Presence | High-intent page has no actionable CTA. | Medium |
| EN-02 | CTA Reachability | Important CTA target is demonstrably unreachable, such as an observed 4xx/5xx response. | High |
| EN-03 | CTA Clarity | CTA wording materially conflicts with the destination purpose. | High |
| EN-04 | Value Proposition Clarity | High-intent page lacks directly observable offering, audience, or use context. | Medium |
| EN-05 | Decision Information | A fact required for the identified journey is demonstrably absent from inspected evidence. | Medium |
| EN-06 | Contact / Action Path | Core-service page has no appropriate discoverable route to its expected action. | High |
| EN-07 | Form Actionability | Important form lacks a required purpose, submit control, or submission path. | Medium |
| EN-08 | Follow-up Path | Journey requires follow-up information but no relevant FAQ, help, documentation, or support path is found. | Medium |
| EN-09 | Stable Direct URL | Important opaque or interaction-dependent action has no usable direct target. | Medium |
| EN-10 | Content / Action Consistency | Page promise materially conflicts with the destination or action purpose. | High |
| EN-11 | AI-Readable Action Context | Important interaction-dependent action has no meaningful textual representation or context. | Medium |
| EN-12 | Conversion-Path Completeness | An explicitly defined journey is missing one or more required steps. | High |

## Check Rules

### EN-01 — Primary CTA Presence

Flag only when a deterministically high-intent page has no actionable CTA.

Do not flag ordinary informational pages solely because they lack a CTA.

### EN-02 — CTA Reachability

Flag only when an important CTA target is demonstrably unreachable.

If target status cannot be established, treat it as `UNKNOWN`.

### EN-03 — CTA Clarity

Flag only when there is a deterministic and material mismatch between CTA wording and destination purpose.

Do not make subjective judgments about wording.

### EN-04 — Value Proposition Clarity

Use directly extracted page content such as title, H1, H2, metadata, and relevant text.

Do not infer that information is missing merely because it is absent from one extracted field.

### EN-05 — Decision Information

Evaluate only information established as necessary for the identified journey.

Failure to extract a fact is not automatically proof that the fact is absent.

### EN-06 — Contact / Action Path

The expected action must match the page intent, such as purchase, booking, contact, demo, application, or support.

### EN-07 — Form Actionability

Evaluate only forms identified as important.

Do not require form fields or targets that cannot be justified by the identified journey.

### EN-08 — Follow-up Path

Require a follow-up path only when the journey demonstrably needs additional information.

Do not require FAQ, help, or support links on every page.

### EN-09 — Stable Direct URL

Flag only important actions that depend on an opaque interaction and have no usable direct target.

Do not flag ordinary buttons merely because they do not expose a URL.

### EN-10 — Content / Action Consistency

Flag only when the page promise materially conflicts with the destination or action purpose.

Minor wording differences are not sufficient.

### EN-11 — AI-Readable Action Context

Flag only when an important action is demonstrably dependent on visual or interaction context and lacks meaningful textual representation.

### EN-12 — Conversion-Path Completeness

Evaluate only explicitly established customer journeys.

Do not invent required journey steps.

## Finding Output

Each triggered check must be converted to the shared `Finding` structure.

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

Evidence must identify the observed page or action and the specific fact that triggered the check.

## Severity

- **Critical:** Severe, demonstrably blocked core action.
- **High:** Major core-journey failure or materially misleading action.
- **Medium:** Meaningful actionability or decision-information issue.
- **Low:** Minor issue.

Use the lowest severity supported by the evidence.

## Boundaries

Engagement Audit does not own:

- Crawling mechanics
- Generic broken-link detection
- Metadata or JSON-LD validation
- Orchestration
- Cross-skill deduplication
- Proprietary search or ranking algorithms

## Quality Gate

A valid Engagement Audit finding must follow this traceable path:

`PageResult -> P3 normalization -> EN check -> canonical Finding`

Every finding must be deterministic, reproducible, and evidence-backed.

When required evidence is unavailable, return `UNKNOWN` rather than inventing a finding.
