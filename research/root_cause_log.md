# P3 Root-Cause Log

This log records reusable root causes discovered during P3 research and
quality testing.

A root cause is included only when it can be translated into a reusable
check.

| ID | Root Cause | Evidence Pattern | Boundary | Resulting Check | Confidence |
|---|---|---|---|---|---|
| FR-RC-01 | Stale time-sensitive content | Explicit old date attached to information presented as current | Date alone is insufficient | Flag only when date + current-context evidence exists | High |
| FR-RC-02 | Weak freshness evidence | Missing or weak date signal | Missing date does not prove staleness | Treat as weak signal only | High |
| FR-RC-03 | First-party contradiction | Same fact type has incompatible values across relevant pages | Values must describe same subject/fact | Emit consistency finding | High |
| FR-RC-04 | Normalization error | Same underlying value represented differently | Formatting variation is not contradiction | Normalize before comparison | High |
| FR-RC-05 | Entity-resolution uncertainty | Identity differs across visible/metadata/structured signals | Difference alone does not prove multiple entities | Emit verification-needed ambiguity | Medium |
| FR-RC-06 | Corroboration scope error | Same claim repeated across multiple site pages | First-party repetition is not external proof | Label as on-site corroboration only | High |
| EN-RC-01 | Insufficient deep-page context | Deep page lacks sufficient subject/company/action context | Context requirement depends on page purpose | Check context on actionable deep pages | High |
| EN-RC-02 | Context-insensitive CTA rule | CTA absent on a page | Not every page requires a CTA | Require CTA only when an onward action is expected | High |
| EN-RC-03 | Over-aggressive dead-end detection | No links on page | No-link page can be legitimate | Require actionable-page context before flagging | High |
| EN-RC-04 | Rendering-context limitation | Text data insufficient to assess visual quality | Raw text cannot prove visual presentation | Mark for rendering verification | High |

---

# Detailed Root Causes

## FR-RC-01 — Stale Time-Sensitive Content

### Observation

A page contains an explicit date associated with information that appears to
remain current after the date has passed.

### Evidence

Required:

- explicit date
- audit date
- contextual relationship between the date and current claim

### Boundary

Do not classify the page as stale merely because an old date exists.

Examples of dates that may not indicate stale content:

- historical publication dates
- founding dates
- archived events
- copyright years
- historical references

### Resulting check

`potentially_stale_dated_content`

---

## FR-RC-02 — Weak Freshness Evidence

### Observation

A page lacks an explicit update date.

### Interpretation

This is insufficient evidence to claim that the content is stale.

### Resulting rule

Missing date → weak signal.

Missing date + independently established stale claim → potentially actionable.

---

## FR-RC-03 — First-Party Contradiction

### Observation

The same factual field has incompatible values across pages.

Examples:

- founding year 2018 vs 2020
- phone A vs phone B
- email A vs email B

### Required boundary

The values must describe:

1. the same subject
2. the same fact type
3. incompatible values

### Resulting check

Cross-page consistency analysis.

---

## FR-RC-04 — Normalization Error

### Observation

A detector treats formatting differences as factual contradictions.

### Examples

`+91 9876543210`

and

`+91-987-654-3210`

may represent the same phone number.

### Resulting rule

Normalize before comparison.

---

## FR-RC-05 — Entity Resolution Uncertainty

### Observation

Visible text, metadata and structured data contain different identity
signals.

### Boundary

Different strings do not automatically mean different organizations.

### Resulting check

`potential_entity_ambiguity`

with:

`verification_status = needs_context_verification`

---

## FR-RC-06 — Corroboration Scope Error

### Observation

The same claim appears on multiple first-party pages.

### Correct interpretation

This increases on-site support but does not constitute independent external
corroboration.

### Resulting check

`multi_page_support_available`

with:

`verification_status = on_site_only`

---

## EN-RC-01 — Insufficient Deep-Page Context

### Observation

A visitor may land directly on a deep page without enough information to
understand the organization, subject or next action.

### Resulting check

`limited_page_context`

or a more specific contextual finding.

---

## EN-RC-02 — Context-Insensitive CTA Rule

### Observation

A generic rule flags every page without a CTA.

### Why this is wrong

CTA requirements depend on page intent.

### Resulting rule

Only flag missing CTA when:

- the page is action-oriented
- an onward action is reasonably expected
- no appropriate CTA or navigation path exists

---

## EN-RC-03 — Over-Aggressive Dead-End Detection

### Observation

A page contains no links.

### Why this is insufficient

A page can legitimately be informational or terminal.

### Resulting rule

No links ≠ dead end.

---

## EN-RC-04 — Rendering-Context Limitation

### Observation

Raw PageResult text does not contain enough information to determine
visual presentation.

### Resulting rule

Do not infer:

- poor layout
- poor visual hierarchy
- button prominence
- above-fold placement

from raw text alone.
