# Brand AI Readiness Audit

A portable Agent Skill Marketplace for auditing whether a public website can be
found, understood, trusted, and acted on by search systems, AI assistants, and
direct visitors.

## Skills

- **Audit Orchestrator**: composes specialists, validates findings, deduplicates
  them, and emits the final report.
- **Crawl Render Audit**: checks crawlability, robots, sitemap coverage, HTTP
  responses, redirects, metadata, canonicals, JSON-LD, render-only content,
  entity signals, and cross-page evidence.
- **Engagement Audit**: checks direct-page orientation, context retention,
  decision information, relevant CTAs, contact paths, and internal discovery.
- **Freshness Corroboration**: evaluates supported date signals conservatively.
- **AI Discoverability Audit**: checks machine-readable answerability, structured-data versus visible facts, entity consistency, and proactive AI-readiness opportunities.

## Architecture

```text
URL -> bounded crawler/renderer -> PageResult/site evidence
                                  |       |       |       |       |
                         technical  engagement freshness entity  AI-discoverability
                                  \       |       |       |       /
                              normalize -> deduplicate -> report
```

## Setup and execution

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium  # optional browser rendering
PYTHONPATH=. .venv/bin/python -m skills.crawl_render_audit.scripts.audit https://example.com
```

For the canonical marketplace report:

```bash
PYTHONPATH=. .venv/bin/python -c 'from skills.audit_orchestrator import audit_site_report; import json, sys; print(json.dumps(audit_site_report(sys.argv[1]), indent=2))' https://example.com
```

The bounded crawl is designed for a typical audit in under five minutes;
network speed and optional browser rendering affect the actual duration.

## Output

`audit_site_report` always includes `site`, UTC `audited_at`, `summary` counts,
and `findings`. Each finding has a stable ID, source skill, URL, category,
severity, concrete evidence, and a prioritized `suggested_action`. Coverage
metadata is included when the crawler provides it.

## Safety and limits

The marketplace is recommend-only and read-only. It uses unauthenticated
requests, honors robots.txt, stays on the target host, applies page/depth
limits, does not submit forms, and never modifies a live website. Findings are
evidence-backed; missing optional SEO files or missing dates alone are not
reported as defects.

## Testing

```bash
PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -q
```
## Round 3 hardening status

The entrypoint now composes technical, freshness, engagement, AI-discoverability, render-semantic, and cross-page consistency findings. Reports include coverage, confidence/evidence-strength distributions, and a transparent heuristic readiness score. The crawler uses adaptive high-value URL prioritization, request/runtime/render budgets, robots enforcement, and read-only behavior. Generalization fixtures cover healthy, JS-heavy, commerce, stale, conflict, and engagement scenarios.

Known intentional limitations: independent external corroboration is not asserted unless an external evidence provider is added; missing `llms.txt` is not treated as a defect; missing dates are not treated as proof of staleness; and client-side rendering is treated as a risk only when the rendered-only evidence appears materially decision-relevant.
