from collections.abc import Callable, Iterable

from shared.severity_policy import validate_finding
from .deduplication import deduplicate_findings
from .report_builder import build_report
from skills.crawl_render_audit.scripts.finding_adapter import (
    findings_for_page,
)
from skills.crawl_render_audit.scripts.models import PageResult
from skills.crawl_render_audit.scripts.crawler import WebsiteCrawler
from skills.engagement_audit import findings_for_page as engagement_findings_for_page
from skills.freshness_corroboration import findings_for_page as freshness_findings_for_page


Finding = dict
FindingProvider = Callable[[str], Iterable[Finding]]
FreshnessProvider = Callable[[PageResult], Iterable[Finding]]
PageFindingProvider = Callable[[PageResult], Iterable[Finding]]


def freshness_stub(page: PageResult) -> list[Finding]:
    """Legacy opt-out provider retained for callers that disable freshness."""
    return []


def engagement_stub(url: str) -> list[Finding]:
    """Legacy opt-out provider retained for callers that disable engagement."""
    return []


def _validate_findings(findings: Iterable[Finding]) -> list[Finding]:
    validated = []

    for finding in findings:
        validated.append(validate_finding(finding))

    return validated


def audit_site(
    url: str,
    crawler: WebsiteCrawler | None = None,
    freshness_provider: FreshnessProvider = freshness_findings_for_page,
    engagement_provider: PageFindingProvider = engagement_findings_for_page,
) -> list[Finding]:
    """Crawl a site and return validated findings from all audit providers."""
    site_crawler = crawler or WebsiteCrawler(
        max_pages=10,
        max_depth=2,
    )
    crawl_result = site_crawler.crawl(url)
    pages = _pages_from_crawl(crawl_result)
    return _findings_for_pages(pages, freshness_provider, engagement_provider)


def audit_site_report(
    url: str,
    crawler: WebsiteCrawler | None = None,
    freshness_provider: FreshnessProvider = freshness_findings_for_page,
    engagement_provider: PageFindingProvider = engagement_findings_for_page,
) -> dict:
    """Run the audit and wrap its findings in the canonical report."""
    site_crawler = crawler or WebsiteCrawler(max_pages=10, max_depth=2)
    crawl_result = site_crawler.crawl(url)
    pages = _pages_from_crawl(crawl_result)
    findings = _findings_for_pages(pages, freshness_provider, engagement_provider)
    coverage = {"pages_audited": len(pages)}
    if isinstance(crawl_result, dict):
        coverage.update({
            "pages_discovered": crawl_result.get("pages_discovered", len(pages)),
            "robots": crawl_result.get("robots", {}),
            "sitemaps": crawl_result.get("sitemaps", {}),
        })
    return build_report(url, findings, coverage=coverage)


def _pages_from_crawl(crawl_result: object) -> list[PageResult]:
    if isinstance(crawl_result, dict):
        return crawl_result.get("pages", [])
    return crawl_result


def _findings_for_pages(
    pages: list[PageResult],
    freshness_provider: FreshnessProvider,
    engagement_provider: PageFindingProvider,
) -> list[Finding]:
    findings = [
        finding
        for page in pages
        for finding in findings_for_page(page)
    ]
    findings.extend(
        finding
        for page in pages
        for finding in freshness_provider(page)
    )
    findings.extend(
        finding
        for page in pages
        for finding in engagement_provider(page)
    )
    return deduplicate_findings(_validate_findings(findings))
