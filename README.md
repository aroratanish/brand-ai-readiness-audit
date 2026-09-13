# Brand AI Readiness Audit

A portable Agent Skill Marketplace for auditing whether a public website can be
**found, understood, trusted, and acted on** by search systems, AI assistants,
and direct visitors.

## Why this marketplace exists

Round 3 is about encoding the reasoning behind AI discoverability and on-site
engagement into reusable skills. The marketplace is deliberately deterministic,
evidence-backed, bounded, and read-only. It reports problems and prioritized
fixes; it never changes a live site.

## Skills

- **Audit Orchestrator** — composes all specialists, validates and deduplicates
  findings, ranks fixes by impact/effort, builds the readiness score, referral
  journey, evidence graph, and final report.
- **Crawl Render Audit** — checks crawlability, robots, sitemap coverage, HTTP
  responses, redirects, metadata, canonicals, JSON-LD, render-only content,
  entity signals, and cross-page evidence.
- **Engagement Audit** — checks orientation, context retention, decision paths,
  relevant CTAs, contact paths, forms, and actionable destinations.
- **Freshness Corroboration** — evaluates supported date signals, offer and
  availability consistency, and conservative policy freshness signals.
- **AI Discoverability Audit** — checks machine-readable answerability,
  structured-data versus visible facts, entity consistency, and proactive
  AI-readiness opportunities.

## Architecture

```text
URL
 │
 ▼
Bounded adaptive crawler + optional renderer
 │
 ▼
PageResult / site evidence
 │
 ├── technical checks
 ├── engagement checks
 ├── freshness / corroboration checks
 ├── AI discoverability / answerability
 ├── semantic render analysis
 └── cross-page fact consistency
 │
 ▼
Validation → deduplication → confidence/evidence strength
 │
 ├── AI referral journey
 ├── evidence graph + conflict edges
 ├── impact × effort action ranking
 └── transparent readiness score
 │
 ▼
Single structured audit report
```

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium  # optional browser rendering
```

## Run

Canonical marketplace report:

```bash
PYTHONPATH=. python -c 'from skills.audit_orchestrator import audit_site_report; import json, sys; print(json.dumps(audit_site_report(sys.argv[1]), indent=2))' https://example.com
```

The crawl is bounded by page, depth, request, render, and wall-clock budgets.
The default configuration is designed for a typical audit to stay below five
minutes; actual duration depends on network and optional browser rendering.

## Competitive report layers

### AI Referral Journey

The report estimates five stages:

`discovery → understanding → trust → decision → conversion`

Each stage includes the evidence used to calculate its score and identifies the
lowest-scoring bottleneck.

### Evidence Graph

The report exposes page → entity → commercial-fact relationships and marks
conflicting structured prices with explicit `conflicts_with` edges. This makes
a machine-misrepresentation risk traceable to the pages that created it.

### Impact × Effort ranking

Every finding receives transparent `impact_score`, `effort_score`, and
`priority_score` values. The top actions are also copied into a compact
`recommendations` section so an evaluator can immediately see what to fix first.

### Independent external corroboration

Corroboration is **opt-in** because the core marketplace must remain portable
without an external service. When enabled, the bounded provider checks only a
small number of already-linked public external HTML pages, respects their
`robots.txt`, excludes social/tracker/private hosts, and never treats absence of
corroboration as a defect.

```python
report = audit_site_report(url, enable_external_corroboration=True)
```

## Output

The report includes the required `site`, UTC `audited_at`, severity summary,
and finding list. Findings contain evidence, severity, confidence, suggested
action, and ranking metadata. Additional sections include coverage,
`readiness_score`, `referral_journey`, `evidence_graph`, `recommendations`, and
`external_corroboration`.

## Safety and limits

- Recommend-only and read-only.
- No form submission or authenticated actions.
- Respects `robots.txt` for the target crawl and for opt-in external
  corroboration.
- Same-host page crawling only.
- Bounded requests, pages, depth, rendering, and runtime.
- No trained model weights or required external AI service.
- Missing dates or missing `llms.txt` are not automatically treated as defects.
- First-party repetition is not claimed as independent corroboration.

## Testing

Run the full suite:

```bash
PYTHONPATH=. python -m pytest
```

The current suite covers **119 tests plus 7 subtests**, including adversarial
false-positive cases and generalized fixture sites.

Static final-submission audit:

```bash
PYTHONPATH=. python scripts/final_submission_audit.py
```

Bounded real-site benchmark:

```bash
PYTHONPATH=. python scripts/benchmark_real_sites.py
```

Deterministic local end-to-end smoke benchmark (useful when outbound HTTP is
blocked):

```bash
PYTHONPATH=. python scripts/benchmark_local_e2e.py
```

The benchmark uses Adobe, Python, Wikipedia, and NASA as public targets and
caps each audit to five pages, depth one, thirty requests, and 45 seconds with
browser rendering disabled for a repeatable baseline. If a local environment
blocks outbound HTTP, the script records that limitation rather than treating
network failure as an audit finding.

## Submission structure

```text
brand-ai-readiness-audit/
├── marketplace.json
├── README.md
├── PROGRESS.md
├── requirements.txt
├── shared/
├── skills/
└── tests/
```

The marketplace manifest has exactly one entrypoint and every listed skill has
its own `SKILL.md`.
