from collections.abc import Mapping


SEVERITY_ORDER = ("critical", "high", "medium", "low")


def _finding_sort_key(finding: Mapping[str, object]) -> tuple[int, str, str]:
    severity = finding.get("severity")
    rank = SEVERITY_ORDER.index(severity) if severity in SEVERITY_ORDER else len(SEVERITY_ORDER)
    return rank, str(finding.get("title", "")), str(finding.get("id", ""))


def format_report(report: Mapping[str, object]) -> str:
    """Render a canonical report as deterministic plain text."""
    summary = report.get("summary", {})
    score = report.get("score", {})
    dimensions = score.get("dimensions", {}) if isinstance(score, Mapping) else {}
    findings = report.get("findings", [])

    lines = [
        "BRAND AI READINESS AUDIT",
        "",
        f"Site: {report.get('site', '')}",
        f"Audited at: {report.get('audited_at', '')}",
        f"Overall score: {score.get('overall', 'n/a')}/100",
        "",
        "Dimension scores:",
    ]
    for dimension, value in dimensions.items():
        lines.append(f"- {dimension}: {value}/100")

    lines.extend([
        "",
        "Finding counts:",
    ])
    for severity in SEVERITY_ORDER:
        lines.append(f"- {severity.capitalize()}: {summary.get(severity, 0)}")

    lines.extend(["", "Top issues:"])
    sorted_findings = sorted(findings, key=_finding_sort_key)
    if not sorted_findings:
        lines.append("- None")
    else:
        for finding in sorted_findings:
            action = finding.get("suggested_action", {})
            lines.extend([
                f"- [{finding.get('severity', 'unknown').upper()}] {finding.get('title', '')}",
                f"  URL: {finding.get('url', '')}",
                f"  Evidence: {finding.get('evidence', '')}",
                f"  Why it matters: {finding.get('why_it_matters', '')}",
                f"  Suggested action: {action.get('summary', '')}",
            ])

    return "\n".join(lines)