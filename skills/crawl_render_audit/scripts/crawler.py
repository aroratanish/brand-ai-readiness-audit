from collections import deque

from .models import PageResult
from .url_utils import (
    normalize_url,
    get_domain,
)
from .http_checker import fetch_page
from .html_parser import parse_html


class WebsiteCrawler:

    def __init__(
        self,
        max_pages: int = 30,
        max_depth: int = 3,
    ):
        self.max_pages = max_pages
        self.max_depth = max_depth

    def crawl(self, start_url: str):

        start_url = normalize_url(start_url)
        base_domain = get_domain(start_url)

        queue = deque(
            [(start_url, 0)]
        )

        visited = set()
        pages = []

        while queue and len(pages) < self.max_pages:

            current_url, depth = queue.popleft()

            current_url = normalize_url(current_url)

            if current_url in visited:
                continue

            if depth > self.max_depth:
                continue

            visited.add(current_url)

            print(
                f"[CRAWL] depth={depth} "
                f"url={current_url}"
            )

            response = fetch_page(current_url)

            page = PageResult(
                url=current_url,
                depth=depth,
                status_code=response["status_code"],
                final_url=response["final_url"],
                redirect_chain=response["redirect_chain"],
                raw_html=response["html"],
            )

            if not response["success"]:
                page.errors.append(
                    response["error"]
                )

                pages.append(page)
                continue

            if response["html"]:

                parsed = parse_html(
                    response["html"],
                    response["final_url"] or current_url,
                )

                page.title = parsed["title"]
                page.meta_description = parsed[
                    "meta_description"
                ]

                page.h1 = parsed["h1"]
                page.h2 = parsed["h2"]

                page.canonical = parsed[
                    "canonical"
                ]

                page.internal_links = parsed[
                    "internal_links"
                ]

                page.external_links = parsed[
                    "external_links"
                ]

                page.json_ld = parsed[
                    "json_ld"
                ]

                if depth < self.max_depth:

                    for link in page.internal_links:

                        link = normalize_url(link)

                        if (
                            get_domain(link)
                            == base_domain
                            and link not in visited
                        ):
                            queue.append(
                                (link, depth + 1)
                            )

            pages.append(page)

        return pages