# Product Contract

## Purpose

Brand AI Readiness Audit evaluates whether a public brand website is prepared
for machine discovery, interpretation, trust review, freshness review, and
visitor action. It produces evidence-backed recommendations from a bounded,
read-only crawl.

## Supported dimensions

- **Discoverability:** crawl access, HTTP responses, metadata, headings,
  canonicals, structured data, rendering differences, and machine-readable
  page signals.
- **Freshness:** supported publication/modification dates and explicit stale or
  conflicting first-party signals.
- **Engagement:** page orientation, context retention, relevant action paths,
  contact paths, and actionable controls where the page evidence supports the
  conclusion.
- **Trust:** conservative entity identity comparisons between visible page
  signals and Organization structured data.

## Findings

A finding is a deterministic, reproducible observation with concrete evidence,
severity, impact explanation, and a prioritized suggested action. Findings are
validated and deduplicated before reporting or scoring.

## Severity

Severity uses the shared `critical`, `high`, `medium`, and `low` policy. It
represents impact, not implementation effort. Critical findings require
concrete evidence.

## Final report

The report communicates the audited site, UTC audit time, coverage when
available, severity counts, final findings, and an explainable readiness score.

## Explicit non-claims

The product does not measure actual search or LLM rankings, guaranteed AI
visibility, citation probability, conversion rates, or independent external
corroboration. A readiness score summarizes inspected evidence; it is not a
market ranking or a guarantee of future behavior.