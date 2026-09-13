# Round 3 Progress — Brand AI Readiness Audit

## Submission status

The repository is at **submission-candidate / final-polish stage** for Round 3.
The core marketplace flow is implemented, the specialist skills are wired into
the orchestrator, and the repository has deterministic regression coverage.

### Current validation

- Full pytest suite passes, including the engagement evidence-gating regressions.
- Python source compilation succeeds.
- Static final-submission audit passes the repository validation checks.
- The repository contains exactly one marketplace entrypoint.
- The final implementation includes bounded crawl/render, engagement, freshness,
  entity/trust, AI discoverability, deduplication, scoring, report generation,
  and optional corroboration without requiring a proprietary API.

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
 ├─ AI Discoverability
 └─ Entity / Trust
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
- Documented false-positive research cases and reusable root-cause boundaries.

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

## Current structure

```text
marketplace.json
README.md
requirements.txt

skills/
  crawl_render_audit/
    SKILL.md
    references/
    scripts/
      audit.py                  # Crawl-render JSON CLI
      canonical_analyzer.py
      crawler.py                # Bounded crawl and robots/sitemap flow
      cross_signal_analyzer.py
      entity_analyzer.py        # Visible/schema entity comparison
      evidence_aggregator.py
      finding_adapter.py       # PageResult-to-finding adapter
      html_parser.py           # Metadata, links, headings, JSON-LD
      http_checker.py          # HTTP requests and status handling
      jsonld_analyzer.py
      link_checker.py
      llm_discoverability_analyzer.py
      metadata_analyzer.py
      models.py                # PageResult and LinkResult
      page_type_classifier.py
      render_diff_analyzer.py
      renderer.py              # Optional Playwright rendering
      robots_checker.py
      sitemap_checker.py
      url_utils.py
  audit_orchestrator/
    SKILL.md
    cli.py                # Canonical JSON/text report CLI
    orchestrator.py       # Public audit_site/audit_site_report pipeline
    deduplication.py
    report_builder.py     # Summary, score, and coverage report
    references/
  freshness_corroboration/
    SKILL.md
    SKILL_P3.md
    detector.py           # Active PageResult freshness provider
    rules.py              # Date parsing and false-positive rules
    references/
    scripts/freshness_checks.py  # Normalized logical check helpers
  engagement_audit/
    SKILL.md
    SKILL_P3.md
    __init__.py
    detector.py           # Active PageResult engagement provider
    references/
    scripts/engagement_adapter.py
    scripts/engagement_checks.py  # Normalized logical check helpers
shared/
  product_contract.md
  finding_schema.md
  report_schema.md
  scoring.py             # Deterministic 0-100 scoring
  scoring_rules.md
  report_formatter.py    # Dependency-free human-readable report
  severity_rules.md
  severity_policy.py
  false_positive_boundaries.md
  engagement_boundaries.md
tests/
  test_audit_orchestrator.py
  test_crawler_regressions.py
  test_finding_adapter.py
  test_finding_deduplication.py
  test_false_positive_boundaries.py
  test_freshness_corroboration.py
  test_freshness_checks.py
  test_engagement_checks.py
  test_person2_analyzers.py
  test_realistic_fixtures.py
  test_report_builder.py
  test_report_formatter.py
  test_round3_integration.py
  test_scoring.py
  test_severity_policy.py
```

## Release-Clean / Current Limitations

- Core dependencies are reproducible in `requirements.txt`; Playwright remains an optional browser-rendering dependency.
- HTTP 4xx/5xx responses are represented as failed `PageResult` entries with status and error evidence. Redirects and sub-400 responses remain successful.
- The active freshness and engagement providers use conservative raw `PageResult` detectors. The richer `scripts/` helpers require normalized logical evidence and are not direct orchestrator providers.
- Entity/trust analysis is intentionally narrow: it compares visible identity signals with Organization/Corporation/Brand JSON-LD when available.
- The formatter labels all findings as top issues rather than applying a fixed top-N limit.

## Future Scope

- External corroboration services
- Persistent audit storage
- Dashboards and richer presentation
- Authentication and deployment infrastructure
- Actual search or LLM ranking measurement
- Broader adaptive page-type sampling and entity reconciliation
