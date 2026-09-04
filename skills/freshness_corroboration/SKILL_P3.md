---
name: freshness-corroboration
description: Audit customer-facing website information for demonstrable staleness, expiry, contradiction, and corroboration failures. Use deterministic evidence from page content, structured data, dates, and first-party cross-page comparisons; do not infer freshness from visual appearance alone.
license: your-choice
---

# Freshness Corroboration

## Purpose

Audit a website for concrete freshness and information-trust problems. The skill converts deterministic checks into findings that follow the shared finding contract.

This skill covers the freshness half of the Round-2 problem:
- stale time-sensitive information
- expired offers/events still presented as active
- conflicting first-party facts
- structured-data versus visible-content contradictions
- weak or missing recency/provenance signals when recency is genuinely relevant

It must work from mechanisms that generalize to unseen websites rather than from memorized example sites.

## Inputs

The skill may receive a normalized page/site representation produced by the crawler. Adapt the repository's actual `PageResult` fields to the following logical inputs; do not require these exact field names at the crawler boundary.

### Page-level evidence

- `url`: audited page URL.
- `published_at`: visible/structured publication date when available.
- `modified_at`: visible/structured modification date when available.
- `valid_through` / `expiry_date`: explicit offer/event/policy validity date when available.
- `presented_as_active`: whether the page currently presents the offer/event/information as active.
- `visible_value`: important value extracted from visible page content.
- `structured_value`: corresponding value extracted from JSON-LD/structured data.
- `first_party_prices`: comparable price observations with URL and value.
- `first_party_availability`: comparable availability observations with URL and value.
- `first_party_facts`: comparable important facts with URL and value.
- `sitemap_lastmod`: sitemap modification timestamp when available.
- `time_sensitive_claims`: claims containing current/now/latest/available or equivalent temporal language.

The adapter should pass only evidence actually observed. Missing data is not proof of a defect.

## Procedure

1. Determine whether the content is time-sensitive.
2. Run deterministic checks only where the required evidence exists.
3. Preserve the exact observed values, dates, URLs, and comparison result.
4. Distinguish an absence of evidence from evidence of a problem.
5. Convert triggered checks into the shared finding schema.
6. Assign severity according to the rules below.
7. Return findings to the orchestrator; do not own orchestration or deduplication.

## Deterministic checks

### FR-01 — Update-date presence

Trigger only when content is demonstrably time-sensitive and there is no usable publication/modification/validity signal.

Do not flag an evergreen page merely because it has no date.

### FR-02 — Published/modified consistency

Compare independently observed publication and modification dates. Trigger when the dates materially contradict each other or an impossible chronology is demonstrated.

### FR-03 — Offer/event expiry

Compare an explicit expiry/valid-through date with the audit date. Trigger when the date has passed and the page still presents the item as active.

### FR-04 — Price corroboration

Compare current first-party price observations for the same product/service. Trigger when the values conflict and the observations are sufficiently comparable.

### FR-05 — Availability corroboration

Compare current first-party availability observations for the same product/service. Trigger on a demonstrated contradiction.

### FR-06 — Sitemap corroboration

Compare sitemap `lastmod` against page-level freshness signals. A mismatch alone is not sufficient; require supporting evidence that the sitemap signal materially misrepresents freshness.

### FR-07 — Structured-data corroboration

Compare an important structured-data value against the corresponding visible value. Trigger on a material mismatch.

### FR-08 — Policy freshness

For policies or terms with explicit effective/update dates, detect demonstrated outdatedness or contradiction. Do not infer that a policy is stale solely from its age.

### FR-09 — Cross-page factual consistency

Compare the same important first-party fact across relevant pages. Trigger when materially different values are simultaneously presented without an explanatory context.

### FR-10 — Time-sensitive claim qualification

For claims using language such as `current`, `now`, `latest`, or `available`, require sufficient evidence to establish currency. Missing supporting evidence can be a finding only when the claim is clearly time-sensitive and the absence materially affects trust.

## Finding contract

Every emitted finding must conform to the repository's shared finding schema:

- `id`
- `source_skill`: `freshness-corroboration`
- `url`
- `category`: `freshness`
- `title`
- `severity`: `critical`, `high`, `medium`, or `low`
- `evidence`
- `why_it_matters`
- `suggested_action` with a concise action summary and priority

Evidence must be concrete enough for another auditor to reproduce the finding.

## Severity

- **critical** — business-critical information is demonstrably incorrect, such as materially wrong price/availability or severe misinformation.
- **high** — broad or important trust problem supported by strong contradiction or expiry evidence.
- **medium** — narrower actionable freshness/corroboration problem.
- **low** — limited optimization where the evidence is real but impact is small.

Use the lower severity when the available evidence does not justify a stronger classification.

## Output rules

For each triggered check, emit one structured finding with:

1. what was checked;
2. the exact observed evidence;
3. why the evidence matters;
4. a specific remediation;
5. a priority consistent with severity.

Do not emit prose-only opinions.

## Non-goals and ownership boundaries

Do not duplicate:

- robots.txt compliance;
- HTTP/crawl status handling;
- general link crawling;
- canonical/meta-tag validation;
- generic JSON-LD syntax validation;
- marketplace orchestration;
- cross-skill deduplication.

A technical failure belongs to the crawler/technical audit unless the freshness skill has additional evidence showing a distinct freshness problem.

## References and implementation

Use the accompanying `references/` files for check definitions and research rationale. Use `scripts/freshness_checks.py` for dependency-free deterministic helpers. The orchestrator should adapt real crawler output into the logical inputs above.
