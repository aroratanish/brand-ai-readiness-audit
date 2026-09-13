# Engagement Audit — P3 Check Catalogue

The catalogue defines the intended EN-01 through EN-12 checks. Runtime checks
must never report a condition for which the current `PageResult` evidence is
insufficient.

## Evidence policy

- `UNKNOWN` is not the same as absent or failed.
- Page-level HTML and crawler link results are the current concrete evidence sources.
- Upstream semantic fields may activate gated checks only when explicitly supplied.
- No check may fabricate intent, importance, required facts, destination purpose, or journey steps.
- Generic technical link failures remain owned by the crawl layer unless an engagement consequence is separately established.

| ID | Check | Current evidence support | Trigger | Default severity |
|---|---|---|---|---|
| EN-01 | Primary CTA / Next Action Presence | **Runtime supported with page-type context** | Action-oriented page has no extracted link, button, or form. | Medium |
| EN-02 | Action Target Reachability | **Runtime supported when status/target is observed** | Important/action-oriented target is observed as 4xx/5xx or empty/fragment-only. | High |
| EN-03 | Action Label Presence | **Runtime supported** | Extracted link/button has no text, aria-label, or title. | Medium |
| EN-04 | Page-Level Descriptive Context | **Runtime supported with page-type context** | Action-oriented page has no title, meta description, H1, or H2. Unclassified/informational pages remain UNKNOWN. | Medium |
| EN-05 | Decision Information | Gated | Explicit required facts intersect explicit missing facts. | Medium |
| EN-06 | Expected Action Path | Gated | Explicit expected action path is absent. | High |
| EN-07 | Form Actionability | **Runtime supported at HTML level** | Extracted form has no standard submit control. | Medium |
| EN-08 | Follow-up Path | Gated | Explicit follow-up requirement has no supplied path. | Medium |
| EN-09 | Stable Direct URL | Gated | Explicitly important opaque action lacks a direct representation. | Medium |
| EN-10 | Content / Action Consistency | Gated | Upstream evidence explicitly establishes material mismatch. | High |
| EN-11 | AI-Readable Action Context | Gated by importance | Explicitly important action has no textual/accessibility label. | Medium |
| EN-12 | Conversion-Path Completeness | Gated | Explicit required journey steps are missing. | High |

## Implementation boundary

The runtime implementation intentionally covers the subset that can be
reliably established from the current repository's `PageResult` plus
per-link `LinkResult` evidence. The remaining checks remain deterministic
extension points rather than speculative heuristics.

This is preferable to pretending that unavailable semantics are known.

## False-positive boundaries

1. A historical/reporting date is not automatically a freshness date.
2. An event date is not automatically a page publication/update date.
3. A missing publication date is not proof of stale content.
4. `Contact Sales`, free trials, demos, quotes, and signups are legitimate
   engagement paths.
5. A page with no internal links may be an intentional terminal page.

Research evidence is recorded in `research/false_positive_log.md`.
