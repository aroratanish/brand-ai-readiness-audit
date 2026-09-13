# Brand AI Readiness Scoring Rules

The score is a deterministic summary of final deduplicated findings. It is an
audit-readiness indicator, not a search ranking, LLM score, or guarantee of
citation.

## Method

- Start at `100` for every implemented dimension and the overall score.
- Apply one penalty per final finding using its severity:
  - `critical`: 25 points
  - `high`: 12 points
  - `medium`: 5 points
  - `low`: 2 points
- Clamp every result to the inclusive range `0..100`.
- Score only the findings supplied to the scorer. The orchestrator supplies
  final deduplicated findings, so duplicates are not double-penalized.
- Findings are assigned to dimensions by implemented category:
  - `discoverability`, `structured-data`, and `crawl-render-audit` ->
    `discoverability`
  - `freshness` -> `freshness`
  - `engagement` -> `engagement`
  - `entity-trust` and `trust` -> `trust`
- Unknown categories affect the overall score but do not create an invented
  dimension score.

The overall score is `100` minus all finding penalties. A dimension score is
`100` minus penalties for findings assigned to that dimension. Zero findings
therefore produce an overall score of `100` and dimension scores of `100`.