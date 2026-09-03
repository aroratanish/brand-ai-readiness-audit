from collections import deque

from .models import PageResult
from .url_utils import (
    normalize_url,
    get_hostname,
    is_http_url,
)
from .http_checker import HTTPClient
from .html_parser import parse_html
from .robots_checker import RobotsPolicy


class WebsiteCrawler:

    def __init__(
        self,
        max_pages: int = 30,
        max_depth: int = 3,
    ):

        self.max_pages = max_pages
        self.max_depth = max_depth

        self.client = HTTPClient()

    def crawl(
        self,
        start_url: str
    ):

        start_url = normalize_url(
            start_url
        )

        if not is_http_url(start_url):
            raise ValueError(
                "Start URL must use "
                "http or https."
            )

        base_hostname = get_hostname(
            start_url
        )

        robots = RobotsPolicy(
            start_url,
            self.client
        )

        queue = deque(
            [(start_url, 0)]
        )

        visited = set()
        pages = []

        while (
            queue
            and len(pages)
            < self.max_pages
        ):

            current_url, depth = (
                queue.popleft()
            )

            current_url = normalize_url(
                current_url
            )

            if not current_url:
                continue

            if current_url in visited:
                continue

            if depth > self.max_depth:
                continue

            if get_hostname(
                current_url
            ) != base_hostname:
                continue

            # IMPORTANT:
            # Check robots BEFORE requesting page.
            if not robots.can_fetch(
                current_url
            ):
                print(
                    f"[ROBOTS BLOCKED] "
                    f"{current_url}"
                )
                continue

            visited.add(current_url)

            print(
                f"[CRAWL] "
                f"depth={depth} "
                f"url={current_url}"
            )

            response = self.client.fetch(
                current_url
            )

            page = PageResult(
                url=current_url,
                depth=depth,
                status_code=response[
                    "status_code"
                ],
                final_url=response[
                    "final_url"
                ],
                redirect_chain=response[
                    "redirect_chain"
                ],
                raw_html=response[
                    "html"
                ],
            )

            if not response["success"]:

                page.errors.append(
                    response["error"]
                )

                pages.append(page)
                continue

            # Don't parse PDFs/images/etc.
            if not response["is_html"]:

                pages.append(page)
                continue

            parsed = parse_html(
                response["html"],
                response["final_url"]
                or current_url,
            )

            page.title = parsed[
                "title"
            ]

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

                    link = normalize_url(
                        link
                    )

                    if not link:
                        continue

                    if link in visited:
                        continue

                    if get_hostname(
                        link
                    ) != base_hostname:
                        continue

                    if not robots.can_fetch(
                        link
                    ):
                        print(
                            f"[ROBOTS BLOCKED] "
                            f"{link}"
                        )
                        continue

                    queue.append(
                        (
                            link,
                            depth + 1
                        )
                    )

            pages.append(page)

        return {
            "pages": pages,
            "robots": robots.to_dict(),
            "pages_discovered": len(
                visited
            ),
            "pages_crawled": len(
                pages
            ),
        }