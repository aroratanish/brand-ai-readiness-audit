import json
import sys
from dataclasses import asdict

from .crawler import WebsiteCrawler
from .evidence_aggregator import TechnicalEvidenceAggregator
from .llm_discoverability_analyzer import LLMDiscoverabilityAnalyzer


def run_audit(url: str):
    crawler = WebsiteCrawler(
        max_pages=10,
        max_depth=2,
    )

    crawl_result = crawler.crawl(url)

    pages = crawl_result["pages"]

    evidence_aggregator = TechnicalEvidenceAggregator()

    technical_evidence = evidence_aggregator.aggregate(
        pages,
        crawl_result,
    )

    llm_analyzer = LLMDiscoverabilityAnalyzer()

    llm_discoverability = llm_analyzer.analyze_site(
        url,
        pages,
    )

    technical_evidence["llm_discoverability"] = (
        llm_discoverability
    )

    result = {
        "skill": "crawl-render-audit",
        "version": "0.1.0",
        "site": url,

        "summary": {
            "pages_discovered": (
                crawl_result["pages_discovered"]
            ),
            "pages_crawled": (
                crawl_result["pages_crawled"]
            ),
        },

        "robots": crawl_result["robots"],

        "sitemaps": crawl_result["sitemaps"],

        "technical_evidence": technical_evidence,

        "pages": [
            asdict(page)
            for page in pages
        ],
    }

    return result


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(
            "Usage: "
            "python -m "
            "skills.crawl_render_audit.scripts.audit "
            "https://example.com"
        )
        sys.exit(1)

    url = sys.argv[1]

    result = run_audit(url)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )