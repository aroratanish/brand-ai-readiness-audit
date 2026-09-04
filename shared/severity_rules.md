# Severity Rules

Severity represents the impact of a finding, not the difficulty of implementing
its fix.

## Critical

- Completely prevents crawling or accessibility of important content.
- Causes materially incorrect price information.
- Causes materially incorrect availability information.
- Creates serious business-critical misinformation risk.

Critical severity requires concrete evidence.

## High

- Significant and broad impact.
- Major reduction in discoverability.
- Prevents users or AI systems from finding important information.
- Significant structured-data or trust problems.

## Medium

- Real and actionable issue with narrower impact.
- Examples include missing meta descriptions, missing or incorrect canonical tags,
  missing structured data, heading issues, and broken internal links affecting
  specific pages.

## Low

- Minor issue, optimization, or polish.
- Limited impact on users, search engines, or AI systems.

## Assignment Guidance

- Severity values must be lowercase: `critical`, `high`, `medium`, or `low`.
- Critical findings require concrete evidence.
- Severity represents impact, not implementation difficulty.
- Similar issues should receive consistent severity.
- When uncertain, use the lower severity unless higher severity is supported by
  evidence.
- `suggested_action.priority` should normally match `severity`.
