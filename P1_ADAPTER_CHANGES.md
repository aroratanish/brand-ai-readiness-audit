# P1 Adapter Changes

Implemented the PageResult-to-Finding adapter.

## Changes

- Added `finding_adapter.py` with reusable finding construction.
- Added checks for missing meta descriptions, JSON-LD, and canonicals.
- Added normalized incorrect-canonical detection.
- Integrated findings into the audit CLI output.
- Updated `PROGRESS.md` and completed the shared finding schema documentation.

## Deferred

- Broken internal-link detection remains deferred because `PageResult` does not include per-link HTTP status codes.
- The orchestrator and P3 skills were not implemented.
- P2 crawler code was left unchanged.

## Validation

- Adapter checks passed.
- `example.com` produced the expected missing meta description, JSON-LD, and canonical findings.
- Python compilation passed with the configured workspace interpreter.
