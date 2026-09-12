# False-Positive Boundaries

This specification defines shared boundaries for the P3 `freshness-corroboration`
and `engagement-audit` skills. It prevents a single weak signal from becoming an
unsupported finding when the `PageResult` data does not establish the page's
semantic context.

## Explicit Boundaries

### FP-01: Historical/reporting dates

A historical or annual report may contain old years such as FY2025 versus
FY2024. A historical or reporting-period date describes the subject matter of
the report, not necessarily the age of the page content. It must not
automatically be treated as stale content.

### FP-02: Event dates

Event structured data fields such as `startDate` and `endDate` describe the
event itself, not the publication or update date of the page. Event dates must
not automatically trigger freshness findings.

### FP-03: Missing publication date

A page without an article-style publication or update date is not automatically
stale. The page type and purpose must be considered before deciding whether
freshness evidence is expected or whether a finding is supported.

### FP-04: Sales-assisted CTA

`Talk to Sales` and `Contact Sales` can be valid calls to action for enterprise
offerings. They must not automatically be classified as weak or invalid
engagement CTAs.

### FP-05: Trial/demo/signup CTA

`Try for free`, demo, signup, quote, and similar actions can be valid
engagement or conversion paths depending on the offering and the user's
journey. Their presence must be evaluated in context rather than rejected by a
universal CTA rule.

### FP-06: No internal links

A page with zero internal links is not automatically a dead end. Some pages are
intentionally terminal steps in a user journey, such as payment-success or
confirmation pages.

## Engineering Rules

1. Never classify a date as stale solely because the date is old.
2. Determine the semantic role of a date before using it for freshness.
3. A missing publication or update date alone is insufficient evidence of
   staleness.
4. Do not use a universal CTA rule; consider page purpose and offering.
5. Recognize sales, trial, demo, signup, quote, and similar legitimate
   conversion paths.
6. Zero internal links alone is insufficient evidence of a dead-end finding.
7. If the available `PageResult` data is insufficient to establish the required
   semantic context, prefer no finding over an unsupported finding.
8. These boundaries must be reflected in automated tests when P3
   implementations are added.

## Implementation and Test Contract

Freshness and engagement implementations must use corroborating evidence and
must preserve the semantic distinctions above. A future automated test suite
for the P3 skills must include coverage for FP-01 through FP-06, including
negative assertions that the described cases do not produce unsupported
findings.

This document is a shared specification only. It does not implement freshness
or engagement logic and does not change the existing P1/P2 behavior.
