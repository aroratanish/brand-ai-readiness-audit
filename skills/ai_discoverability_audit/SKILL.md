---
name: ai-discoverability-audit
description: Audit machine-readable identity, answerability, structured-data consistency, and cross-page factual signals that affect AI discoverability. Use after crawling a public website; read-only and evidence-backed.
license: MIT
---

# AI Discoverability Audit

## When to use
Use for a crawled public website when checking whether important facts are easy for machine readers and AI assistants to identify, quote, and distinguish from conflicting signals.

## Inputs
- One or more `PageResult` objects from the crawl/render skill.

## Procedure
1. Inspect visible text, headings, JSON-LD, links, and rendered-content evidence.
2. Detect only evidence-backed machine-readability problems; do not treat missing optional files such as `llms.txt` as defects.
3. Compare high-value structured facts with visible page facts when both are available.
4. Compare organization identity and product facts across crawled pages when enough evidence exists.
5. Emit prioritized recommendations and separate proactive opportunities from detected defects.

## Output
Return findings using the shared finding schema. Every defect must include concrete page/site evidence and a severity. Opportunities must be clearly labeled as opportunities rather than defects.
