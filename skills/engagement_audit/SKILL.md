---
name: engagement-audit
description: Evaluate whether direct visitors can understand a page and take an appropriate next action.
---

# Engagement Audit

## When to use
Use on crawled `PageResult` objects, especially homepages, decision pages,
articles, contact pages, and deep URLs likely to receive AI referrals.

## Inputs
A `PageResult` containing URL, depth, raw HTML, headings, and links.

## Procedure
Classify page intent from URL and crawl context, extract visible text and
actions, then check orientation, context retention, relevant next action,
contact path, and internal discovery. Suppress conversion findings on
informational pages where no action is expected.

## Outputs
`findings_for_page(page)` returns canonical findings with concrete evidence,
severity, and a prioritized suggested action.

## Safety
Read-only HTML inspection only. Never submit forms, authenticate, or modify a
live website.
