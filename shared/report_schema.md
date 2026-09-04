# Report Schema

Audit reports use this canonical structure:

```json
{
  "site": "example.com",
  "audited_at": "2026-09-03T10:00:00Z",
  "summary": {
    "total_findings": 6,
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 0
  },
  "findings": [
    {
      "id": "F-001",
      "source_skill": "crawl-render-audit",
      "url": "https://example.com/product/123",
      "category": "discoverability",
      "title": "Missing meta description",
      "severity": "medium",
      "evidence": "No description found",
      "why_it_matters": "Search engines and AI tools rely on this for summaries.",
      "suggested_action": {
        "summary": "Add a concise meta description.",
        "priority": "medium"
      }
    }
  ]
}
```

## Field Definitions

| Field | Type | Required | Purpose |
| --- | --- | --- | --- |
| `site` | string | Yes | Lowercase hostname or domain of the audited site, such as `example.com`. |
| `audited_at` | string | Yes | UTC timestamp in machine-readable ISO-8601 format, using a `Z` suffix. |
| `summary` | object | Yes | Counts of the findings in the report by severity. |
| `summary.total_findings` | integer | Yes | Total number of findings in `findings`. |
| `summary.critical` | integer | Yes | Number of findings with `critical` severity, including zero. |
| `summary.high` | integer | Yes | Number of findings with `high` severity, including zero. |
| `summary.medium` | integer | Yes | Number of findings with `medium` severity, including zero. |
| `summary.low` | integer | Yes | Number of findings with `low` severity, including zero. |
| `findings` | array of finding objects | Yes | Final deduplicated findings using the schema in `finding_schema.md`. |

Summary values are calculated from the actual findings and are not hardcoded.
The report builder validates each finding severity using the shared severity
policy before counting it.
