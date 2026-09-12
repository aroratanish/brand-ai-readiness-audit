---
name: crawl-render-audit
description: Crawl a public website and collect deterministic discoverability, rendering, and coverage evidence.
---

# Crawl Render Audit

## When to use
Use as the technical specialist for an arbitrary public HTTP(S) website.

## Inputs
A site URL and bounded crawl settings such as maximum pages and depth.

## Procedure
Normalize URLs, fetch same-host pages, consult robots.txt and sitemaps, record
redirects and link responses, parse metadata, headings, canonicals, JSON-LD, and
raw HTML, and optionally compare browser-rendered HTML with the raw response.

## Outputs
Returns `PageResult` objects and crawl coverage/evidence. The shared finding
adapter turns deterministic observations into canonical findings; absence of
optional `llms.txt` is not a defect by itself.

## Safety
Read-only, unauthenticated, rate-bounded inspection. Do not submit forms,
execute authenticated actions, bypass robots, or alter the target site.