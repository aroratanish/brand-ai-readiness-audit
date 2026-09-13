# Round 3 Progress — Brand AI Readiness Audit

## Submission status

The repository is at **submission-candidate / final-polish stage** for Round 3.
The core marketplace flow is implemented, the specialist skills are wired into
the orchestrator, and the repository has deterministic regression coverage.

### Current validation

- Full pytest suite passes, including the engagement evidence-gating regressions.
- The test count is intentionally reported by the test runner rather than hard-coded in this document.
- Python source compilation succeeds.
- Static final-submission audit passes **17/17** checks.
- The repository contains exactly one marketplace entrypoint.

## Implemented architecture

```text
URL
 ↓
Bounded crawler / optional renderer
 ↓
PageResult
 ↓
Specialist evidence + checks
 ├─ Crawl / Render
 ├─ Engagement
 ├─ Freshness / Corroboration
 └─ AI Discoverability
 ↓
Validation → deduplication → ranking
 ↓
Readiness score + referral journey + evidence graph
 ↓
Structured audit report
```

## P3 individual work — Engagement

Completed:

- Deterministic engagement adapter from the repository's real `PageResult`.
- HTML evidence extraction for links, buttons, forms, headings, title and meta description.
- Reuse of crawler `LinkResult` status/redirect/error evidence where available.
- Conservative EN-01–EN-12 check catalogue with explicit evidence gates.
- Runtime integration through `skills.engagement_audit.findings_for_page`.
- Canonical finding output and severity normalization through the existing orchestrator.
- False-positive boundaries for sales CTAs, trials, terminal pages and contextual action requirements.
- Regression and integration tests for supported and unknown-evidence cases.

The important design decision is that unsupported semantics remain gated rather
than being guessed from keywords or missing extraction fields.

## Freshness / research work

Completed repository work includes:

- Conservative freshness checks for supported date signals.
- Expiry, structured-vs-visible value, first-party consistency and policy signals.
- Historical-date and event-date false-positive boundaries.
- Missing-date-is-not-stale boundary.
- Six documented false-positive research cases and reusable root-cause boundaries.

## P1 / P2 / shared repository capabilities

The current repository also contains:

- bounded crawling and rendering;
- robots and sitemap handling;
- metadata, canonical and JSON-LD analysis;
- page-type classification;
- cross-page entity and commercial-fact consistency;
- AI answerability/discoverability checks;
- deterministic deduplication;
- severity normalization;
- scoring and action ranking;
- AI referral journey reporting;
- evidence graph generation;
- opt-in bounded external corroboration;
- adversarial/generalization fixtures and regression tests;
- benchmark and final-submission validation scripts.

## Known limitations — intentionally bounded

- Visual UX quality cannot be established from raw HTML alone.
- Unsupported journey semantics remain `UNKNOWN` rather than being inferred.
- External corroboration is optional and bounded to already-linked public HTML pages.
- The public-site benchmark depends on outbound network availability in the execution environment.
- The marketplace remains a read-only audit/reporting system; it does not modify customer websites.

These are documented scope boundaries, not hidden implementation failures.

## Final pre-submission commands

```bash
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python scripts/final_submission_audit.py
PYTHONPATH=. python scripts/benchmark_local_e2e.py
```

For a network-enabled environment, also run:

```bash
PYTHONPATH=. python scripts/benchmark_real_sites.py
```
