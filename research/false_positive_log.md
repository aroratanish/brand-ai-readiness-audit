# P3 False-Positive Log

This file records cases where a seemingly reasonable audit rule can produce
an incorrect finding.

The purpose is to establish explicit boundaries for P3 checks.

---

## FP-001 — Missing Date ≠ Stale

### Trigger

A page has no published or updated date.

### Naive Finding

"Content is stale."

### Correct Result

False positive.

### Reason

Absence of a date does not establish that the information is old.

### Rule Change

Do not emit a stale-content finding from a missing date alone.

### Related Root Cause

FR-RC-02

---

## FP-002 — Historical Date ≠ Expired Content

### Trigger

A page contains an old historical date such as:

"Company founded in 2010."

### Naive Finding

"Page contains stale information."

### Correct Result

False positive.

### Reason

The date describes a historical fact rather than current information.

### Rule Change

Only evaluate dates for freshness when the date is semantically attached to
time-sensitive information.

### Related Root Cause

FR-RC-01

---

## FP-003 — Different Phone Formatting ≠ Different Phone Number

### Trigger

Two pages contain:

`+91 9876543210`

and

`+91-987-654-3210`

### Naive Finding

"Conflicting phone numbers."

### Correct Result

False positive.

### Reason

The values may represent the same phone number.

### Rule Change

Normalize phone values before comparison.

### Related Root Cause

FR-RC-04

---

## FP-004 — Different Email Addresses Can Be Legitimate

### Trigger

About page:

`hello@example.com`

Contact page:

`support@example.com`

### Naive Finding

"Incorrect contact information."

### Correct Result

Potential issue, not confirmed contradiction.

### Reason

Different addresses can legitimately serve different purposes.

### Rule Change

Require contextual evidence before treating different emails as a factual
contradiction.

### Related Root Cause

FR-RC-03

---

## FP-005 — Missing CTA on Informational Page

### Trigger

An article page contains no purchase, signup or contact CTA.

### Naive Finding

"Weak engagement / missing CTA."

### Correct Result

False positive unless the page's purpose requires an onward action.

### Reason

Informational pages can legitimately direct users through related content
rather than conversion actions.

### Rule Change

CTA checks must be contextual.

### Related Root Cause

EN-RC-02

---

## FP-006 — No Links ≠ Dead End

### Trigger

A page contains no internal links.

### Naive Finding

"Dead-end page."

### Correct Result

Needs contextual verification.

### Reason

Some pages may legitimately be terminal or may expose actions outside the
captured link data.

### Rule Change

Require evidence that the page represents an actionable journey before
flagging a dead end.

### Related Root Cause

EN-RC-03

---

## FP-007 — Raw Text Cannot Prove Visual Defect

### Trigger

PageResult contains little text.

### Naive Finding

"Poor visual hierarchy."

### Correct Result

Do not emit a visual finding.

### Reason

Raw text does not establish layout, visibility or above-fold presentation.

### Rule Change

Mark the observation as requiring rendering context.

### Related Root Cause

EN-RC-04

---

## FP-008 — Different Entity Strings Do Not Automatically Mean Multiple Entities

### Trigger

Metadata contains one organization name while visible text contains a
brand/product/subsidiary name.

### Naive Finding

"Entity ambiguity."

### Correct Result

Potential ambiguity requiring verification.

### Reason

Brands, subsidiaries and legal entities can legitimately have different
names.

### Rule Change

Require contextual evidence before reporting confirmed entity ambiguity.

### Related Root Cause

FR-RC-05

---

## FP-009 — Repeated First-Party Evidence Is Not External Corroboration

### Trigger

The same claim appears on About, Contact and Services pages.

### Naive Finding

"Claim independently corroborated."

### Correct Result

False positive if described as independent corroboration.

### Reason

All evidence originates from the same first-party website.

### Rule Change

Label this as:

`verification_status = on_site_only`

### Related Root Cause

FR-RC-06

---

## FP-010 — Low Text Volume Is Not Automatically a Defect

### Trigger

A page contains less than an arbitrary amount of text.

### Naive Finding

"Insufficient content."

### Correct Result

Needs contextual verification.

### Reason

Landing pages, contact pages and application pages may intentionally use
short copy.

### Rule Change

Use page purpose and available context rather than text length alone.

### Related Root Cause

EN-RC-01

---

# False-Positive Policy

A P3 rule must not produce a confirmed defect when its evidence only shows:

- absence of optional metadata
- absence of a generic CTA
- absence of links
- old historical dates
- harmless formatting variation
- different but contextually legitimate identity strings
- repeated first-party evidence
- insufficient rendering information

When evidence is incomplete, prefer:

`needs_context_verification`

over a confirmed defect.

---

# Quality Principle

The P3 audit should follow:

Deterministic evidence
        ↓
Context
        ↓
Root cause
        ↓
Finding
        ↓
Recommendation

Never:

Missing signal
        ↓
Assume defect
