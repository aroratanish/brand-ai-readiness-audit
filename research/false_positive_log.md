# False-Positive Research Log

## Purpose

This document records legitimate website patterns that could be
incorrectly flagged by the freshness or engagement audit rules.

The research is intended to establish semantic boundaries for the
audit rules and reduce false positives.

These examples are research evidence. They do not by themselves prove
that the implementation code passes every case. Implementation
correctness must be verified separately through unit/integration tests.

Assigned false-positive cases:

- FP-01 — Historical Date
- FP-02 — Event Date
- FP-03 — Missing Publication Date ≠ Stale Content
- FP-04 — Talk to Sales Can Be a Valid CTA
- FP-05 — Free Trial Can Be a Valid Engagement Path
- FP-06 — No Internal Links ≠ Dead End


---

# FP-01 — Historical Date

## Potential Audit Rule

Flag content as stale when an old year or historical date is detected.

## Actual Observation

**Site:** Microsoft  
**Page:** 2025 Annual Report / Investor Relations  
**URL:** https://www.microsoft.com/investor/reports/ar25/

Microsoft's investor materials identify a Fiscal Year 2025 Annual
Report and provide the report as a financial-reporting document.

Annual reports naturally contain historical reporting periods,
including comparisons between fiscal years.

## Why the Naive Rule Would Flag It

A freshness checker based only on detected years or dates could
interpret an older year appearing in the document as the publication
or update date.

For example, a reference to Fiscal Year 2024 could be incorrectly
treated as evidence that the page itself is from 2024.

## Why It Is Legitimate

The year may describe the subject matter of the document rather than
the date on which the web content was published or updated.

A historical reporting period is therefore not sufficient evidence of
staleness.

## Required Boundary

Historical dates, reporting periods, and dates describing the subject
matter must not automatically be treated as freshness signals.

Freshness logic should distinguish between:

- publication dates
- last-modified/update dates
- expiration/validity dates
- historical reporting periods
- dates describing events or subject matter

Only semantically relevant freshness dates should be used to establish
staleness.

## Relevant Root Cause

**FR-RC-01 — Stale time-sensitive content**

## Evidence

Microsoft Investor Relations / 2025 Annual Report:

https://www.microsoft.com/investor/reports/ar25/

The Microsoft investor site explicitly identifies the Fiscal Year 2025
Annual Report, demonstrating that years appearing in investor
documents can represent reporting periods rather than page freshness
metadata.


---

# FP-02 — Event Date

## Potential Audit Rule

Treat a detected event date as the publication or update date of the
content and use it as evidence of freshness or staleness.

## Actual Observation

**Site:** Google Search Central  
**Page:** Event structured-data documentation  
**URL:** https://developers.google.com/search/docs/appearance/structured-data/event

Google's Event structured-data documentation defines event properties
including:

- `startDate`
- `endDate`
- `previousStartDate`

These properties describe when an event occurs or changes schedule.

## Why the Naive Rule Would Flag It

A generic date-extraction rule could detect a value such as:

`2025-07-21`

and incorrectly assume that this is the publication or last-update
date of the documentation page.

## Why It Is Legitimate

The date belongs to the event represented by the structured data.

It does not necessarily describe when the documentation itself was
published or modified.

## Required Boundary

Event dates must not automatically be interpreted as page publication
or update dates.

Freshness evaluation must distinguish dates describing:

- the page/document
- an event
- a product/service
- a reporting period
- another subject represented by the page

## Relevant Root Cause

**FR-RC-01 — Stale time-sensitive content**

## Evidence

Google Search Central — Event structured data:

https://developers.google.com/search/docs/appearance/structured-data/event


---

# FP-03 — Missing Publication Date ≠ Stale Content

## Potential Audit Rule

Flag a page as stale when no publication or last-updated date is
detected.

## Actual Observation

**Site:** Amazon Web Services (AWS)  
**Page:** Contact AWS  
**URL:** https://aws.amazon.com/contact-us/

The page is an operational contact/support page.

It provides pathways for:

- sales
- compliance support
- technical support
- account/billing support

The page is not presented as an article or dated publication.

## Why the Naive Rule Would Flag It

A checker that requires a publication date for every page could
interpret the absence of such metadata as evidence that the page is
stale.

## Why It Is Legitimate

Operational pages do not necessarily require article-style
publication metadata.

The page's usefulness comes from its current functional pathways and
support/contact mechanisms, not from a publication timestamp.

## Required Boundary

Missing publication metadata alone must not establish a stale-content
finding.

The audit should first consider:

1. page purpose/type
2. whether the content is time-sensitive
3. whether a freshness date is expected for that page type

A missing date may therefore result in insufficient freshness evidence
rather than a positive stale-content finding.

## Relevant Root Cause

**FR-RC-01 — Stale time-sensitive content**

## Evidence

AWS — Contact AWS:

https://aws.amazon.com/contact-us/

The current page provides active sales and support pathways without
being an article-style dated resource.


---

# FP-04 — Talk to Sales Can Be a Valid CTA

## Potential Audit Rule

Flag a commercial page when its primary CTA does not provide an
immediate self-service conversion action.

## Actual Observation

**Site:** Microsoft  
**Page:** Microsoft 365 E3 for enterprise  
**URL:** https://www.microsoft.com/en-in/microsoft-365/enterprise/e3

The page provides:

- pricing information
- `Contact Sales`
- `Try for free`

for the enterprise offering.

## Why the Naive Rule Would Flag It

A generic CTA checker might assume that a valid commercial CTA must
immediately complete a purchase.

It could therefore incorrectly treat `Contact Sales` as weak or
non-converting.

## Why It Is Legitimate

Enterprise software commonly uses sales-assisted conversion.

A visitor may need:

- organizational discussion
- pricing guidance
- deployment information
- requirements clarification
- enterprise purchasing assistance

Therefore, contacting sales can be the intended next step.

## Required Boundary

CTA evaluation must consider the intended user journey.

The audit should recognize legitimate conversion paths such as:

- Buy
- Purchase
- Contact Sales
- Request Demo
- Get Started
- Sign Up
- Start Trial

A sales-assisted CTA should not automatically be treated as an
engagement failure merely because it does not immediately complete a
purchase.

## Relevant Root Cause

**EN-RC-01 — CTA/action mismatch**

## Evidence

Microsoft 365 E3 for enterprise:

https://www.microsoft.com/en-in/microsoft-365/enterprise/e3

The current page explicitly presents `Contact Sales` as an action for
the enterprise offering.


---

# FP-05 — Free Trial Can Be a Valid Engagement Path

## Potential Audit Rule

Flag a commercial page when it does not provide an immediate purchase
action.

## Actual Observation

**Site:** Microsoft  
**Page:** Microsoft 365 E3 for enterprise  
**URL:** https://www.microsoft.com/en-in/microsoft-365/enterprise/e3

The page presents `Try for free` alongside the enterprise offering and
pricing information.

## Why the Naive Rule Would Flag It

A simplistic engagement rule could require an immediate purchase action
and classify a trial pathway as incomplete.

## Why It Is Legitimate

A free trial is itself a deliberate engagement and conversion
mechanism.

The intended journey can be:

visitor → trial → product evaluation → conversion

Therefore, requiring a direct purchase action would create a false
positive for pages intentionally designed around trial-based
conversion.

## Required Boundary

The audit should recognize legitimate engagement/conversion paths
including:

- free trial
- demo
- signup
- registration
- contact sales
- request quote
- get started

The checker should evaluate whether a meaningful next action exists,
not whether one specific CTA type exists.

## Relevant Root Cause

**EN-RC-01 — CTA/action mismatch**

## Evidence

Microsoft 365 E3 for enterprise:

https://www.microsoft.com/en-in/microsoft-365/enterprise/e3

The page currently exposes `Try for free` as a valid action.


---

# FP-06 — No Internal Links ≠ Dead End

## Potential Audit Rule

Flag a page as a dead-end journey when no internal links are detected.

## Actual Observation

**Site:** Stripe  
**Page:** Payment-success page guidance  
**URL:** https://stripe.com/resources/more/payment-successful-pages

Stripe describes a payment-success page as the screen shown after a
customer completes a transaction and states that it is typically the
final step in the checkout flow.

Stripe's Checkout documentation also documents redirecting customers
to a success page after payment.

## Why the Naive Rule Would Flag It

A rule that equates:

`no internal links`

with:

`dead-end journey`

could incorrectly flag a legitimate terminal page.

## Why It Is Legitimate

Some user journeys intentionally terminate after a successful action.

Examples include:

- payment completion
- order confirmation
- successful submission
- account creation
- transaction completion

A page can therefore be a valid terminal state even when it does not
contain ordinary internal-content navigation.

## Required Boundary

Absence of internal links must not independently establish an
engagement failure.

The audit should consider:

1. page purpose
2. whether the user has already completed the intended action
3. whether the page represents a legitimate terminal state
4. whether a next action is actually expected

A transaction-success page should not be classified as a dead end
merely because the journey has intentionally reached its terminal
state.

## Relevant Root Cause

**EN-RC-02 — Dead-end journey**

## Evidence

Stripe — Payment successful pages:

https://stripe.com/resources/more/payment-successful-pages

Stripe explicitly describes the payment-success page as typically the
final step in the checkout flow.

Stripe Checkout documentation:

https://docs.stripe.com/payments/checkout/custom-success-page

Stripe documents redirecting customers to a success page after
successful Checkout completion.


---

# Research Boundary

These examples establish semantic boundaries for the audit.

They do NOT mean that:

- every page without a date is fresh
- every CTA is valid
- every page without internal links is healthy
- every old year is harmless
- every event date should be ignored

Instead, the examples demonstrate that these signals cannot be
interpreted in isolation.

The audit should evaluate the meaning and context of the evidence before
raising a finding.

# Summary

| ID | False-positive boundary |
|---|---|
| FP-01 | Historical/reporting dates are not automatically freshness dates |
| FP-02 | Event dates are not automatically publication/update dates |
| FP-03 | Missing publication metadata does not automatically mean stale |
| FP-04 | Sales-assisted CTAs can be valid engagement paths |
| FP-05 | Trial/signup/demo paths can be valid conversion paths |
| FP-06 | No internal links does not automatically mean a dead-end journey |
