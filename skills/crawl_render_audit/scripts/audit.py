import json
import sys
from dataclasses import asdict

from .crawler import WebsiteCrawler
from .evidence_aggregator import TechnicalEvidenceAggregator
from .cross_signal_analyzer import CrossSignalAnalyzer
from .page_type_classifier import PageTypeClassifier


def run_audit(url: str):
    crawler = WebsiteCrawler(
        max_pages=10,
        max_depth=2,
    )

    crawl_result = crawler.crawl(url)

    evidence_aggregator = TechnicalEvidenceAggregator()

    technical_evidence = evidence_aggregator.aggregate(
        crawl_result["pages"],
        crawl_result,
    )

    cross_signal_analyzer = CrossSignalAnalyzer()

    cross_signal_evidence = cross_signal_analyzer.analyze_site(
        crawl_result["pages"]
    )

    page_type_classifier = PageTypeClassifier()

    page_type_evidence = page_type_classifier.classify_site(
        crawl_result["pages"]
    )

    result = {
        "skill": "crawl-render-audit",
        "version": "0.1.0",
        "site": url,

        "summary": {
            "pages_discovered": crawl_result[
                "pages_discovered"
            ],
            "pages_crawled": crawl_result[
                "pages_crawled"
            ],
        },

        "robots": crawl_result["robots"],

        "sitemaps": crawl_result["sitemaps"],

        "technical_evidence": technical_evidence,

        "cross_signal_evidence": cross_signal_evidence,

        "page_type_evidence": page_type_evidence,

        "pages": [
            asdict(page)
            for page in crawl_result["pages"]
        ],
    }

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python -m "
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