# P3 Site Sampling Research

## Purpose

Identify reusable freshness, trust, consistency, corroboration and engagement
patterns across different website categories.

The goal is not to memorize individual websites. The goal is to identify
repeatable characteristics that can be converted into deterministic checks.

The sites used for research are development samples, not grading targets.

---

## Research Method

For each sampled website, inspect only a representative subset:

1. Homepage
2. About / company page
3. One representative product/service/deep page
4. Contact page
5. One article, documentation or informational page where available

Record:

- URL
- category
- pages sampled
- freshness evidence
- consistency evidence
- entity/identity evidence
- engagement evidence
- observed issue
- whether the issue is confirmed
- evidence supporting the conclusion
- possible false positive
- useful recommendation
- confidence
- reusable root cause

Do not classify a page as defective merely because a preferred feature is
missing.

---

# Category Coverage

The target research set covers:

| Category | What to investigate |
|---|---|
| E-commerce | product/offer freshness, price/availability, purchase CTA, product context |
| SaaS | pricing/demo freshness, product identity, demo/signup path |
| University | program information, dates, contact details, application paths |
| News | publication/update dates, author/context, article navigation |
| Government | policy dates, official identity, service/contact paths |
| Local business | hours, contact information, location, booking/contact CTA |
| Portfolio | identity clarity, project context, contact path |
| Financial service | rates, policy dates, regulated identity, application/contact path |
| JS-heavy | information visible after rendering but absent from supplied text |
| Poorly optimized | weak context, stale information, contradictory facts, dead ends |
| Unseen/generalization | sites not used while developing individual checks |

---

# Observation Record Format

For every researched site use:

### Site

- URL:
- Category:
- Pages sampled:

### Freshness

- Explicit dates:
- Time-sensitive information:
- Evidence of stale information:
- Confirmed issue:
- Confidence:

### Consistency

- Organization name:
- Address:
- Phone:
- Email:
- Product/service names:
- Policy/version/date claims:
- Contradictions:
- Confirmed issue:
- Confidence:

### Entity Clarity

- Visible organization identity:
- Metadata identity:
- Structured-data identity:
- Ambiguity observed:
- Confirmed issue:
- Confidence:

### Engagement

- First impression:
- Navigation:
- Primary action:
- Deep-page context:
- Dead-end risk:
- Friction:
- Trust signals:
- Confirmed issue:
- Confidence:

### Recommendation

- Problem:
- Evidence:
- Why it matters:
- Specific fix:
- Priority hint:

### Root Cause

- Root-cause ID:
- Generalizable pattern:
- Proposed deterministic check:

---

# Reusable Research Findings

The following patterns should be investigated and validated across the
sampled sites rather than tied to one particular domain.

## Finding R-01 — Stale time-sensitive information

A dated offer, event, rate, policy, product availability statement or other
time-sensitive claim can become misleading when the explicit date has passed.

Evidence requirement:

- An explicit date exists.
- The date is objectively old relative to the audit date.
- The surrounding content indicates that the information is still presented
  as current.

A date by itself is not sufficient evidence of stale content.

Root cause:

FR-RC-01 — stale time-sensitive content.

Proposed check:

Detect explicit dates and require contextual evidence before reporting a
freshness defect.

---

## Finding R-02 — Missing date is not equivalent to stale content

A page without an update date cannot automatically be classified as stale.

This is an important negative finding because missing metadata alone creates
false positives.

Root cause:

FR-RC-02 — weak freshness evidence.

Proposed check:

Treat missing dates as a weak signal only. Do not emit a confirmed stale
finding without additional evidence.

---

## Finding R-03 — Cross-page factual contradiction

If the same organization publishes incompatible values for the same fact
across relevant pages, the contradiction can reduce trust.

Examples:

- different phone numbers
- different email addresses
- different founding years
- incompatible policy dates
- incompatible product/service descriptions

Evidence requirement:

Same subject + same fact type + incompatible values + sufficient context.

Root cause:

FR-RC-03 — first-party contradiction.

Proposed check:

Compare normalized values only when the values represent the same fact.

---

## Finding R-04 — Formatting variation is not necessarily contradiction

Different formatting of the same underlying value should not automatically
produce a finding.

Examples:

- +91 1234567890 vs +91-1234567890
- capitalization differences in names
- harmless whitespace differences

Root cause:

FR-RC-04 — normalization error.

Proposed check:

Normalize values before comparing them.

---

## Finding R-05 — Entity identity inconsistency

Different organization/entity names in visible content, metadata or
structured data may create ambiguity.

However, the presence of different strings alone does not prove that the
site represents multiple entities.

Evidence requirement:

- conflicting identity signals
- sufficient context to establish that they refer to the same entity

Root cause:

FR-RC-05 — entity-resolution uncertainty.

Proposed check:

Report entity ambiguity as a verification-needed observation unless the
identity conflict is sufficiently established.

---

## Finding R-06 — On-site repetition is not independent corroboration

If the same fact appears on several pages, that provides repeated first-party
evidence but does not prove that the fact is externally true.

Root cause:

FR-RC-06 — corroboration scope error.

Proposed check:

Label repeated site evidence as `on_site_only`; never describe it as
independent external verification.

---

## Finding R-07 — Deep pages require independent context

AI systems may send visitors directly to a product, service, article or
documentation page.

A deep page should therefore contain enough information for the visitor to
understand:

- what organization they are visiting
- what the page represents
- why the information matters
- what the next useful action is

Root cause:

EN-RC-01 — insufficient deep-page context.

---

## Finding R-08 — CTA requirements are contextual

Not every page requires the same CTA.

Examples:

- Product page → purchase/request action may be expected.
- SaaS pricing page → signup/demo may be expected.
- Article → related content or informational navigation may be sufficient.
- About page → contact/about navigation may be sufficient.

Root cause:

EN-RC-02 — context-insensitive CTA rule.

Proposed check:

Determine whether an onward action is reasonably expected from the page
purpose before reporting a missing CTA.

---

## Finding R-09 — No links does not automatically mean dead end

Some pages can legitimately contain little or no navigation depending on
their purpose.

Root cause:

EN-RC-03 — over-aggressive dead-end detection.

Proposed check:

Require evidence that the page represents an actionable journey where an
onward path is reasonably expected.

---

## Finding R-10 — Raw text cannot prove visual quality

Raw PageResult text cannot reliably establish:

- visual hierarchy
- above-the-fold placement
- button prominence
- visual contrast
- layout quality

Root cause:

EN-RC-04 — rendering-context limitation.

Proposed check:

Mark such observations as requiring rendering context instead of asserting
a visual defect.

---

# Research-to-Implementation Rule

A research observation should only become a deterministic check when:

1. The observation can be expressed using reusable website characteristics.
2. The required evidence is available from PageResult data.
3. The rule has a clear boundary.
4. The rule can explain why the evidence constitutes a problem.
5. The rule has a corresponding false-positive boundary.

The research must therefore follow:

Observation
→ Evidence
→ Root cause
→ Boundary
→ Deterministic check
→ Recommendation
