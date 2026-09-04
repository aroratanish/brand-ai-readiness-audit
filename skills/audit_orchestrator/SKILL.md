# Audit Orchestrator

## Purpose

Run the shared audit pipeline and return findings from the available audit
providers.

## Interface

Use `skills.audit_orchestrator.audit_site(url)`.

Use `skills.audit_orchestrator.audit_site_report(url)` when the canonical report
envelope is needed. The original findings-list interface remains available.

The input is a site URL. The output is a predictable list of findings using the
canonical structure documented in `shared/finding_schema.md`.

## Responsibilities

- Use the existing P2 `WebsiteCrawler` to obtain `PageResult` objects.
- Pass every `PageResult` through the P1 finding adapter.
- Collect findings from crawl, freshness, and engagement providers.
- Validate and normalize every finding severity before returning findings.
- Deduplicate compatible findings by effective URL, category, and normalized title.
- Preserve each producer's `source_skill` value.
- Build the canonical report envelope from final deduplicated findings when
	`audit_site_report` is used.

## Temporary P3 Stubs

- `freshness_stub(url) -> []`
- `engagement_stub(url) -> []`

The providers are injectable into `audit_site` so the real P3 implementations
can replace them later without changing the pipeline shape.

## Current Limitations

- Freshness and engagement detection are not implemented.
- Findings are not scored, and the report does not provide a score.
- Deduplication is intentionally conservative and does not merge findings with
	different severities.
- Broken internal-link detection remains deferred because `PageResult` does not
	contain per-link HTTP status information.
- P2 HTTP 4xx/5xx handling remains unchanged.
