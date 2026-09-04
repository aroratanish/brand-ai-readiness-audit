from collections.abc import Callable, Iterable

from shared.severity_policy import validate_finding
from .deduplication import deduplicate_findings
from .report_builder import build_report
from skills.crawl_render_audit.scripts.finding_adapter import (
    findings_for_page,
)
from skills.crawl_render_audit.scripts.models import PageResult
from skills.crawl_render_audit.scripts.crawler import WebsiteCrawler


Finding = dict
FindingProvider = Callable[[str], Iterable[Finding]]


def freshness_stub(url: str) -> list[Finding]:
    """Temporary P3 freshness provider; intentionally produces no findings."""
    return []


def engagement_stub(url: str) -> list[Finding]:
    """Temporary P3 engagement provider; intentionally produces no findings."""
    return []


def _validate_findings(findings: Iterable[Finding]) -> list[Finding]:
    validated = []

    for finding in findings:
        validated.append(validate_finding(finding))

    return validated


def audit_site(
    url: str,
    crawler: WebsiteCrawler | None = None,
    freshness_provider: FindingProvider = freshness_stub,
    engagement_provider: FindingProvider = engagement_stub,
) -> list[Finding]:
    """Crawl a site and return validated findings from all audit providers."""
    site_crawler = crawler or WebsiteCrawler(
        max_pages=10,
        max_depth=2,
    )
    pages: list[PageResult] = site_crawler.crawl(url)

    findings = [
        finding
        for page in pages
        for finding in findings_for_page(page)
    ]
    findings.extend(freshness_provider(url))
    findings.extend(engagement_provider(url))

    validated_findings = _validate_findings(findings)
    return deduplicate_findings(validated_findings)


def audit_site_report(
    url: str,
    crawler: WebsiteCrawler | None = None,
    freshness_provider: FindingProvider = freshness_stub,
    engagement_provider: FindingProvider = engagement_stub,
) -> dict:
    """Run the audit and wrap its findings in the canonical report."""
    findings = audit_site(
        url,
        crawler=crawler,
        freshness_provider=freshness_provider,
        engagement_provider=engagement_provider,
    )
    return build_report(url, findings)
