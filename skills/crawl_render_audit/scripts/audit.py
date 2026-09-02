import json
import sys
from dataclasses import asdict

from .crawler import WebsiteCrawler


def run_audit(url: str):

    crawler = WebsiteCrawler(
        max_pages=10,
        max_depth=2,
    )

    pages = crawler.crawl(url)

    result = {
        "site": url,
        "pages": [
            asdict(page)
            for page in pages
        ],
    }

    return result


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(
            "Usage: python -m "
            "skills.crawl-render-audit.scripts.audit "
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