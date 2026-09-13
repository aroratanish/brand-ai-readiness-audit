---
name: audit-orchestrator
description: Compose all read-only website audit skills into one normalized report.
---

# Audit Orchestrator

## When to use
Use for a complete audit of any public HTTP(S) website when one report must
cover discoverability, engagement, freshness, and entity trust.

## Inputs
- `url`: public site URL.
- Optional injected crawler or providers for tests and controlled integrations.

## Procedure
1. Crawl with `WebsiteCrawler`, respecting robots, same-host boundaries, depth,
   page, and request limits.
2. Pass every `PageResult` to crawl/render, freshness, engagement, and entity
   checks.
3. Validate finding fields, normalize severity, and conservatively deduplicate.
4. Rank actions by transparent impact × effort heuristics.
5. Build the AI referral journey, evidence graph, and readiness score.
6. Optionally corroborate against a small bounded set of already-linked public
   external pages.
7. Emit `audit_site_report(url)` with summary counts, coverage, rankings,
   journey, graph, and safety metadata.

## Outputs
`audit_site(url)` returns findings. `audit_site_report(url)` returns the final
marketplace report envelope in `shared/report_schema.md`, including `site`,
`audited_at`, `summary`, `score`, `coverage`, and `findings`, plus readiness
scoring, referral journey, evidence graph, ranked recommendations, and optional
external corroboration. Use `python -m skills.audit_orchestrator.cli URL --format text`
for a human-readable summary.

## Safety
This skill is read-only. It performs unauthenticated inspection, applies crawl
limits, honors robots.txt, never submits forms, and does not modify a live site.
