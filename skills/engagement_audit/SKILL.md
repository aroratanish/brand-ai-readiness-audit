---
name: engagement-audit
description: Evaluate whether action-oriented customer journeys expose clear, reachable, understandable next steps using deterministic PageResult evidence.
---

# Engagement Audit

## Purpose

Evaluate concrete engagement and actionability signals for pages that are
actually expected to support a user journey. The skill is conservative: it
reports only conditions supported by the crawler's `PageResult` and normalized
engagement evidence.

## Inputs

The runtime accepts a crawled `PageResult` containing, where available:

- effective URL, status and redirects;
- raw/rendered HTML;
- title, meta description and headings;
- extracted links and forms;
- per-link `LinkResult` status information;
- deterministic page-type evidence from the crawl pipeline.

The dependency-free checker also accepts normalized evidence fields for future
orchestrators, but it must never invent intent, importance, required facts, or
journey steps.

## Evidence Pipeline

```text
PageResult
   ↓
Engagement adapter
   ↓
Observable links / buttons / forms / page context
   ↓
Deterministic EN checks
   ↓
Canonical Finding
```

The adapter does not crawl, submit forms, authenticate, or fabricate semantic
facts. Existing crawler link results are reused when they are available.

## Deterministic Checks

### EN-01 — Primary CTA / Next Action Presence

Runs only when deterministic upstream page-type evidence establishes an
action-oriented page (currently high-confidence or medium-confidence
`product`, `pricing`, or `contact`). It flags the absence of any extracted
link, button, or form.

Informational and terminal pages are not flagged merely because they contain
few or no actions.

### EN-02 — Action Target Reachability

Uses an observed per-link HTTP status when one exists. It may also flag an
empty or fragment-only action link when the page is action-oriented or the
control is explicitly marked as important/button-like.

Unknown target status is never treated as a failure. Generic link-health
ownership remains with the crawl layer; this check exists for the engagement
consequence of an action target failure.

### EN-03 — Action Label Presence

Flags an extracted link or button only when it has no visible text, `aria-label`,
or `title`. It does not make subjective judgments about whether wording is
persuasive or whether a destination semantically matches the label.

### EN-04 — Page-Level Descriptive Context

On an action-oriented page, flags only when no title, meta description, H1, or
H2 is available from `PageResult` or the adapter's direct HTML fallback.

This is intentionally narrower than claiming that a page lacks a complete
business value proposition.

### EN-05 — Decision Information

Inactive unless an upstream evidence producer explicitly supplies both the
facts established as required and the facts demonstrably missing. Extraction
failure alone is not proof of absence.

### EN-06 — Expected Action Path

Inactive unless upstream evidence explicitly establishes an expected action
path and its absence. The engagement checker does not infer purchase, booking,
demo, contact, or support intent from keywords.

### EN-07 — Form Actionability

Flags an extracted form when no standard submit control is observable. This is
an HTML-level signal, not proof that a JavaScript-controlled form is broken.
The check does not infer form importance from visual appearance or wording.

### EN-08 — Follow-up Path

Inactive unless upstream evidence explicitly establishes that follow-up
information is required and no follow-up path is supplied.

### EN-09 — Stable Direct URL

Inactive unless an upstream producer explicitly marks an action as opaque and
important. A normal button without a URL is not itself a defect.

### EN-10 — Content / Action Consistency

Inactive unless an upstream producer supplies both the page promise and
destination purpose and explicitly establishes a material mismatch.

### EN-11 — AI-Readable Action Context

Flags only explicitly important links/buttons with no extracted text,
`aria-label`, or `title`. The checker does not infer visual-only status.

### EN-12 — Conversion-Path Completeness

Inactive unless an upstream producer explicitly establishes required and
available journey steps. Required steps are never invented by this skill.

## False-Positive Boundaries

The skill must preserve these boundaries:

- `Contact Sales`, `Try for free`, demo, signup, and quote paths can be valid
  commercial actions.
- Missing publication dates do not prove stale content.
- Historical/reporting dates do not automatically represent page freshness.
- Event dates do not automatically represent page freshness.
- No internal links does not prove a dead-end journey.
- Raw HTML does not prove visual layout or above-the-fold quality.

See `research/false_positive_log.md` and the shared boundary documents for the
research rationale.

## Finding Contract

Every emitted finding uses the canonical fields:

- `id`
- `source_skill = "engagement-audit"`
- `url`
- `category = "engagement"`
- `title`
- `severity`
- `evidence`
- `why_it_matters`
- `suggested_action.summary`
- `suggested_action.priority`

Evidence includes the effective page URL and the deterministic observation
that caused the finding.

## Ownership

Engagement Audit does not own crawling, robots.txt, generic metadata or
JSON-LD validation, generic broken-link inventory, orchestration, scoring,
deduplication, or proprietary search/ranking behavior.

## Quality Gate

A finding must be:

- deterministic;
- reproducible;
- evidence-backed;
- attributable to an EN check;
- within engagement ownership.

When required evidence cannot be established, the check returns no finding
rather than converting `UNKNOWN` into failure.

## Safety
Read-only HTML inspection only. Never submit forms, authenticate, or modify a
live website.
