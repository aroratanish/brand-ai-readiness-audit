# Finding Schema

All audit skills must emit findings using this common schema.

## Canonical Finding

```json
{
  "id": "F-001",
  "source_skill": "crawl-render-audit",
  "url": "https://example.com/product/123",
  "category": "discoverability",
  "title": "Missing meta description",
  "severity": "medium",
  "evidence": "No <meta name='description'> found on https://example.com/product/123",
  "why_it_matters": "Search engines and AI tools rely on this for summaries; without it they generate their own, often inaccurately.",
  "suggested_action": {
    "summary": "Add a concise meta description.",
    "priority": "medium"
  }
}
```

## Field Definitions

| Field | Type | Required | Purpose |
| --- | --- | --- | --- |
| `id` | string | Yes | Stable identifier for the finding, such as `F-001`. |
| `source_skill` | string | Yes | Name of the skill that produced the finding. The producing skill assigns this value. |
| `url` | string | Yes | Effective or audited page URL associated with the finding. |
| `category` | string | Yes | Readiness area addressed by the finding, such as `discoverability`, `freshness`, or `engagement`. |
| `title` | string | Yes | Short human-readable description of the issue. |
| `severity` | string | Yes | Impact level. Must be one of `critical`, `high`, `medium`, or `low`, in lowercase. |
| `evidence` | string | Yes | Concrete, specific support for the finding, including affected URLs or observed behavior where applicable. |
| `why_it_matters` | string | Yes | Explanation of the user, business, search, or AI-readiness impact. |
| `suggested_action` | object | Yes | Recommended remediation for the finding. |
| `suggested_action.summary` | string | Yes | Concise description of the recommended remediation. |
| `suggested_action.priority` | string | Yes | Action priority. It should normally match `severity` and uses the same lowercase values. |

## `source_skill` Semantics

The skill that produces a finding assigns its own `source_skill` value. The
orchestrator must preserve that value and must not arbitrarily reassign it.

Current source skills are:

| `source_skill` | Responsibility |
| --- | --- |
| `crawl-render-audit` | Technical crawling and discoverability. |
| `freshness-corroboration` | Freshness and information trust. |
| `engagement-audit` | User and AI engagement and actionability. |

## Severity Values

`severity` is restricted to these lowercase values:

- `critical`
- `high`
- `medium`
- `low`

Severity describes impact, not implementation difficulty. See
[`severity_rules.md`](severity_rules.md) for the definitions and assignment
guidance.