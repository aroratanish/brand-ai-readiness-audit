# Engagement False-Positive Boundaries

This specification defines false-positive boundaries for the P3
`engagement-audit` skill. Engagement findings require evidence about the page's
purpose, offering, and user action paths.

## Explicit Boundaries

### FP-04: Sales-assisted CTA

`Contact Sales`, `Talk to Sales`, and similar sales-assisted actions are valid
engagement paths for enterprise products. Do not classify sales CTAs as
engagement failures without considering the page purpose and offering type.

### FP-05: Trial/demo/signup CTA

`Try for free`, demos, trials, signup flows, quote requests, and similar
actions are valid conversion paths. Do not require a single universal CTA
pattern.

### FP-06: No internal links

A page with zero internal links is not automatically a dead-end journey.
Terminal pages such as payment confirmation, success pages, and completed
workflows may intentionally end user journeys.

## Engineering Principles

1. Engagement failures require evidence of a broken or missing user action path.
2. Absence of one preferred CTA does not prove engagement failure.
3. Page purpose must be considered before producing findings.
4. Prefer no finding over unsupported assumptions.
5. Tests must cover these boundaries before engagement rules are expanded.

This document is a shared specification only. It does not implement engagement
logic and does not modify existing P1, P2, or P3 code.
