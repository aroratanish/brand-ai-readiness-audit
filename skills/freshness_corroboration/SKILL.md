---
name: freshness-corroboration
description: Identify supported stale or conflicting freshness signals without inferring staleness from missing dates.
---

# Freshness Corroboration

## When to use
Use for pages with machine-readable publication or modification dates and for
trust-sensitive facts that need review.

## Inputs
A `PageResult`, optionally with a fixed UTC `as_of` time for deterministic
tests.

## Procedure
Inspect JSON-LD date fields, ignore event dates and report-like historical
objects, parse timezone-aware dates, and compare supported signals to the
freshness threshold. Missing dates are not treated as stale.

## Outputs
`findings_for_page(page)` returns canonical freshness findings only when the
observed evidence supports them.

## Safety
Read-only analysis. Repeated first-party statements are not independent
corroboration, and no external claim is asserted without fetched evidence.
