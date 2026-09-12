import sys
import time
import re
from collections import deque
from urllib.parse import urlparse

from .models import PageResult, LinkResult
from .url_utils import (
    normalize_url,
    get_hostname,
    is_http_url,
)
from .http_checker import HTTPClient
from .html_parser import parse_html
from .robots_checker import RobotsPolicy
from .link_checker import LinkChecker
from .sitemap_checker import SitemapChecker
from .renderer import Renderer
from .render_diff_analyzer import RenderDiffAnalyzer
from .metadata_analyzer import MetadataAnalyzer
from .canonical_analyzer import CanonicalAnalyzer
from .jsonld_analyzer import JSONLDAnalyzer
from .page_type_classifier import PageTypeClassifier


class WebsiteCrawler:

    def __init__(
        self,
        max_pages: int = 30,
        max_depth: int = 3,
        max_requests: int = 120,
        max_seconds: float = 240.0,
        max_rendered_pages: int = 8,
    ):

        self.max_pages = max_pages
        self.max_depth = max_depth
        self.max_requests = max_requests
        self.max_seconds = max_seconds
        self.max_rendered_pages = max_rendered_pages
        self._request_count = 0
        self._rendered_page_count = 0

        self.client = HTTPClient()

        self.link_checker = LinkChecker(
            self.client
        )

        self.renderer = Renderer()

        self.render_diff_analyzer = (
            RenderDiffAnalyzer()
        )

        self.metadata_analyzer = (
            MetadataAnalyzer()
        )

        self.canonical_analyzer = (
            CanonicalAnalyzer()
        )

        self.jsonld_analyzer = (
            JSONLDAnalyzer()
        )
        self.page_type_classifier = PageTypeClassifier()

    @staticmethod
    def _priority(url: str, depth: int) -> tuple[int, int, str]:
        """Prioritize pages likely to contain high-value audit evidence."""
        path = urlparse(url).path.lower()
        score = 0
        patterns = {
            r"^/?$": 100, r"/(product|products|item|items)(/|$)": 90,
            r"/(pricing|plans?|price)(/|$)": 88, r"/(service|services|solution|solutions)(/|$)": 84,
            r"/(contact|contact-us)(/|$)": 80, r"/(about|about-us|company)(/|$)": 72,
            r"/(faq|faqs)(/|$)": 68, r"/(docs?|documentation|help|guides?)(/|$)": 60,
            r"/(blog|article|articles|news|posts?)(/|$)": 40,
        }
        for pattern, weight in patterns.items():
            if re.search(pattern, path):
                score = max(score, weight)
        score += max(0, 20 - depth * 5)
        return (-score, depth, url)

    def _pop_next(self, queue):
        items = list(queue)
        queue.clear()
        if not items:
            return None
        items.sort(key=lambda item: self._priority(item[0], item[1]))
        selected = items.pop(0)
        queue.extend(items)
        return selected

    def crawl(
        self,
        start_url: str
    ):

        # --------------------------------------------------
        # RESET REQUEST BUDGET
        # --------------------------------------------------
        self._request_count = 0
        self._rendered_page_count = 0
        crawl_started = time.monotonic()

        # --------------------------------------------------
        # NORMALIZE START URL
        # --------------------------------------------------

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

        # --------------------------------------------------
        # ROBOTS.TXT
        # --------------------------------------------------

        robots = RobotsPolicy(
            start_url
        )

        # --------------------------------------------------
        # INITIAL QUEUE
        # --------------------------------------------------

        queue = deque()

        queue.append(
            (
                start_url,
                0
            )
        )

        queued = {
            start_url
        }

        visited = set()

        pages = []

        # --------------------------------------------------
        # STATISTICS
        # --------------------------------------------------

        stats = {
            "pages_discovered": 1,
            "pages_queued": 1,
            "pages_crawled": 0,
            "pages_failed": 0,
            "pages_skipped_robots": 0,

            "links_checked": 0,
            "broken_links": 0,
            "redirects": 0,

            "sitemaps_checked": 0,
            "sitemap_urls_discovered": 0,
            "request_budget": self.max_requests,
            "requests_used": 0,
            "request_budget_exhausted": False,
            "runtime_budget_seconds": self.max_seconds,
            "runtime_budget_exhausted": False,
            "render_budget": self.max_rendered_pages,
            "renders_used": 0,
            "render_budget_exhausted": False,
        }

        # --------------------------------------------------
        # SITEMAP DISCOVERY
        # --------------------------------------------------

        sitemap_checker = SitemapChecker()

        sitemap_candidates = []

        # Sitemaps declared inside robots.txt
        for sitemap_url in robots.sitemaps:

            sitemap_url = normalize_url(
                sitemap_url
            )

            if sitemap_url:
                sitemap_candidates.append(
                    sitemap_url
                )

        # Standard sitemap location
        parsed_start_url = urlparse(start_url)
        site_origin = f"{parsed_start_url.scheme}://{parsed_start_url.netloc}"
        standard_sitemap = normalize_url(
            f"{site_origin}/sitemap.xml"
        )

        if standard_sitemap not in sitemap_candidates:

            sitemap_candidates.append(
                standard_sitemap
            )

        # Also try sitemap_index.xml
        sitemap_index = normalize_url(
            f"{site_origin}/sitemap_index.xml"
        )

        if sitemap_index not in sitemap_candidates:

            sitemap_candidates.append(
                sitemap_index
            )

        # --------------------------------------------------
        # CHECK SITEMAPS
        # --------------------------------------------------

        for sitemap_url in sitemap_candidates:

            if (
                len(
                    sitemap_checker.visited_sitemaps
                )
                >= sitemap_checker.max_sitemaps
            ):
                break

            if not is_http_url(
                sitemap_url
            ):
                continue

            if get_hostname(
                sitemap_url
            ) != base_hostname:
                continue

            # Respect robots.txt
            if not robots.can_fetch(
                sitemap_url
            ):
                continue

            sitemap_result = (
                sitemap_checker.parse(
                    sitemap_url
                )
            )

            if not sitemap_result[
                "exists"
            ]:
                continue

            # --------------------------------------------------
            # NORMAL URLSET
            # --------------------------------------------------

            if sitemap_result[
                "type"
            ] == "urlset":

                sitemap_urls = (
                    sitemap_result[
                        "urls"
                    ]
                )

            # --------------------------------------------------
            # SITEMAP INDEX
            # --------------------------------------------------

            elif sitemap_result[
                "type"
            ] == "sitemapindex":

                discovered = (
                    sitemap_checker.discover(
                        sitemap_result[
                            "sitemaps"
                        ]
                    )
                )

                sitemap_urls = (
                    discovered[
                        "urls"
                    ]
                )

            else:

                sitemap_urls = []

            stats[
                "sitemaps_checked"
            ] = len(
                sitemap_checker
                .visited_sitemaps
            )

            stats[
                "sitemap_urls_discovered"
            ] = len(
                sitemap_checker
                .discovered_urls
            )

            # --------------------------------------------------
            # ADD SITEMAP URLS TO QUEUE
            # --------------------------------------------------

            for sitemap_page_url in sitemap_urls:

                sitemap_page_url = (
                    normalize_url(
                        sitemap_page_url
                    )
                )

                if not sitemap_page_url:
                    continue

                # Only crawl same hostname
                if get_hostname(
                    sitemap_page_url
                ) != base_hostname:
                    continue

                # Respect robots
                if not robots.can_fetch(
                    sitemap_page_url
                ):

                    stats[
                        "pages_skipped_robots"
                    ] += 1

                    continue

                if (
                    sitemap_page_url
                    in queued
                ):
                    continue

                if (
                    len(queue)
                    + len(pages)
                    >= self.max_pages
                ):
                    break

                queue.append(
                    (
                        sitemap_page_url,
                        0
                    )
                )

                queued.add(
                    sitemap_page_url
                )

                stats[
                    "pages_queued"
                ] += 1

                stats[
                    "pages_discovered"
                ] += 1

        # --------------------------------------------------
        # MAIN CRAWL LOOP
        # --------------------------------------------------

        while (
            queue
            and len(pages)
            < self.max_pages
        ):

            next_item = self._pop_next(queue)
            if next_item is None:
                break
            current_url, depth = next_item

            if time.monotonic() - crawl_started >= self.max_seconds:
                stats["runtime_budget_exhausted"] = True
                break

            # Already crawled
            if current_url in visited:
                continue

            # Maximum depth
            if depth > self.max_depth:
                continue

            # Same-domain restriction
            if (
                get_hostname(
                    current_url
                )
                != base_hostname
            ):
                continue

            # --------------------------------------------------
            # ROBOTS CHECK
            # --------------------------------------------------

            if not robots.can_fetch(
                current_url
            ):

                print(
                   f"[ROBOTS BLOCKED] "
                   f"{current_url}",
                   file=sys.stderr
                )

                stats[
                    "pages_skipped_robots"
                ] += 1

                visited.add(
                    current_url
                )

                continue

            # --------------------------------------------------
            # MARK VISITED
            # --------------------------------------------------

            visited.add(
                current_url
            )

            print(
                f"[CRAWL] "
                f"depth={depth} "
                f"url={current_url}",
                file=sys.stderr
                )

            # --------------------------------------------------
            # FETCH PAGE
            # --------------------------------------------------

            if self._request_count >= self.max_requests:
                stats["request_budget_exhausted"] = True
                break

            self._request_count += 1
            response = self.client.fetch(
                current_url
            )

            # --------------------------------------------------
            # CREATE PAGE RESULT
            # --------------------------------------------------

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

            # --------------------------------------------------
            # REDIRECT STATISTICS
            # --------------------------------------------------

            if response[
                "redirected"
            ]:

                stats[
                    "redirects"
                ] += 1

            # --------------------------------------------------
            # REQUEST FAILED
            # --------------------------------------------------

            if not response[
                "success"
            ]:

                if response[
                    "error"
                ]:

                    page.errors.append(
                        response[
                            "error"
                        ]
                    )

                stats[
                    "pages_failed"
                ] += 1

                pages.append(
                    page
                )

                continue

            # --------------------------------------------------
            # NON-HTML RESOURCE
            # --------------------------------------------------

            if not response[
                "is_html"
            ]:

                pages.append(
                    page
                )

                stats[
                    "pages_crawled"
                ] += 1

                continue

            # --------------------------------------------------
            # PARSE HTML
            # --------------------------------------------------

            parsed = parse_html(
                response[
                    "html"
                ],

                response[
                    "final_url"
                ]
                or current_url,
            )

            # --------------------------------------------------
            # PAGE METADATA
            # --------------------------------------------------

            page.title = parsed[
                "title"
            ]

            page.meta_description = (
                parsed[
                    "meta_description"
                ]
            )

            page.h1 = parsed[
                "h1"
            ]

            page.h2 = parsed[
                "h2"
            ]

            page.canonical = parsed[
                "canonical"
            ]

            page.internal_links = (
                parsed[
                    "internal_links"
                ]
            )

            page.external_links = (
                parsed[
                    "external_links"
                ]
            )

            page.json_ld = parsed[
                "json_ld"
            ]

            # --------------------------------------------------
            # DETERMINISTIC TECHNICAL ANALYSIS
            # --------------------------------------------------

            page.technical_evidence = {}

            # --------------------------------------------------
            # METADATA ANALYSIS
            # --------------------------------------------------

            page.technical_evidence[
                "metadata"
            ] = self.metadata_analyzer.analyze(
                page.title,
                page.meta_description,
                page.h1,
                page.h2,
            )

            # --------------------------------------------------
            # CANONICAL ANALYSIS
            # --------------------------------------------------

            page.technical_evidence[
                "canonical"
            ] = self.canonical_analyzer.analyze(
                page.final_url or page.url,
                page.canonical,
            )

            # --------------------------------------------------
            # JSON-LD ANALYSIS
            # --------------------------------------------------

            page.technical_evidence[
                "json_ld"
            ] = self.jsonld_analyzer.analyze(
                page.json_ld
            )

            # --------------------------------------------------
            # PAGE TYPE CLASSIFICATION
            # --------------------------------------------------
            page.technical_evidence["page_type"] = self.page_type_classifier.classify(page)

            # --------------------------------------------------
            # BROWSER RENDERING
            # --------------------------------------------------

            render_url = (
                page.final_url
                or page.url
            )

            if self._rendered_page_count >= self.max_rendered_pages:
                stats["render_budget_exhausted"] = True
                page.technical_evidence["render"] = {
                    "status": "skipped",
                    "evidence": {"reason": "render_budget_exhausted", "budget": self.max_rendered_pages},
                }
                render_result = None
            else:
                self._rendered_page_count += 1
                stats["renders_used"] = self._rendered_page_count
                render_result = self.renderer.render(render_url)

            # --------------------------------------------------
            # RENDERING FAILED
            # --------------------------------------------------

            if render_result is not None and render_result.error:

                page.errors.append(
                    f"Renderer: "
                    f"{render_result.error}"
                )

                page.technical_evidence[
                    "render"
                ] = {
                    "status": "error",

                    "evidence": {
                        "url": render_url,
                        "error": (
                            render_result.error
                        ),
                    },
                }

            # --------------------------------------------------
            # RENDERING SUCCESSFUL
            # --------------------------------------------------

            elif render_result is not None:

                page.rendered_html = (
                    render_result.rendered_html
                )

                page.technical_evidence[
                    "render"
                ] = {

                    "status": "success",

                    "evidence": {
                        "url": render_url,

                        "final_url": (
                            render_result.final_url
                        ),

                        "status_code": (
                            render_result.status_code
                        ),

                        "rendered_title": (
                            render_result.title
                        ),

                        "rendered_html_length": (
                            len(
                                render_result
                                .rendered_html
                            )
                        ),
                    },
                }

                # --------------------------------------------------
                # RAW VS RENDERED ANALYSIS
                # --------------------------------------------------

                page.technical_evidence[
                    "raw_vs_rendered"
                ] = (
                    self.render_diff_analyzer.analyze(
                        page.raw_html,
                        page.rendered_html,
                    )
                )

            # --------------------------------------------------
            # INTERNAL LINKS
            # --------------------------------------------------

            for link in page.internal_links:

                link = normalize_url(
                    link
                )

                if not link:
                    continue

                if get_hostname(
                    link
                ) != base_hostname:
                    continue

                # ----------------------------------------------
                # ROBOTS CHECK BEFORE REQUEST
                # ----------------------------------------------

                if not robots.can_fetch(
                    link
                ):

                    print(
                        f"[ROBOTS BLOCKED] "
                        f"{link}"
                    )

                    stats[
                        "pages_skipped_robots"
                    ] += 1

                    continue

                # ----------------------------------------------
                # CHECK LINK
                # ----------------------------------------------
                if self._request_count >= self.max_requests:
                    stats["request_budget_exhausted"] = True
                    break

                self._request_count += 1
                link_result = (
                    self.link_checker.check(
                        link
                    )
                )

                page.link_results.append(
                    LinkResult(
                        url=link_result[
                            "url"
                        ],

                        status_code=(
                            link_result[
                                "status_code"
                            ]
                        ),

                        success=(
                            link_result[
                                "success"
                            ]
                        ),

                        final_url=(
                            link_result[
                                "final_url"
                            ]
                        ),

                        redirected=(
                            link_result[
                                "redirected"
                            ]
                        ),

                        redirect_chain=(
                            link_result[
                                "redirect_chain"
                            ]
                        ),

                        content_type=(
                            link_result[
                                "content_type"
                            ]
                        ),

                        classification=(
                            link_result[
                                "classification"
                            ]
                        ),

                        error=(
                            link_result[
                                "error"
                            ]
                        ),
                    )
                )

                stats[
                    "links_checked"
                ] += 1

                # ----------------------------------------------
                # BROKEN LINK
                # ----------------------------------------------

                if link_result[
                    "classification"
                ] in {
                    "client_error",
                    "server_error",
                    "request_error",
                }:

                    stats[
                        "broken_links"
                    ] += 1

                # ----------------------------------------------
                # REDIRECT
                # ----------------------------------------------

                if link_result[
                    "redirected"
                ]:

                    stats[
                        "redirects"
                    ] += 1

                # ----------------------------------------------
                # ADD TO CRAWL QUEUE
                # ----------------------------------------------

                if (
                    link not in queued
                    and link not in visited
                    and depth < self.max_depth
                ):

                    if (
                        len(queue)
                        + len(pages)
                        < self.max_pages
                    ):

                        queue.append(
                            (
                                link,
                                depth + 1
                            )
                        )

                        queued.add(
                            link
                        )

                        stats[
                            "pages_queued"
                        ] += 1

                        stats[
                            "pages_discovered"
                        ] += 1

            # --------------------------------------------------
            # EXTERNAL LINKS
            # --------------------------------------------------

            for link in page.external_links:

                link = normalize_url(
                    link
                )

                if not link:
                    continue

                link_result = (
                    self.link_checker.check(
                        link
                    )
                )

                page.link_results.append(
                    LinkResult(
                        url=link_result[
                            "url"
                        ],

                        status_code=(
                            link_result[
                                "status_code"
                            ]
                        ),

                        success=(
                            link_result[
                                "success"
                            ]
                        ),

                        final_url=(
                            link_result[
                                "final_url"
                            ]
                        ),

                        redirected=(
                            link_result[
                                "redirected"
                            ]
                        ),

                        redirect_chain=(
                            link_result[
                                "redirect_chain"
                            ]
                        ),

                        content_type=(
                            link_result[
                                "content_type"
                            ]
                        ),

                        classification=(
                            link_result[
                                "classification"
                            ]
                        ),

                        error=(
                            link_result[
                                "error"
                            ]
                        ),
                    )
                )

                stats[
                    "links_checked"
                ] += 1

                if link_result[
                    "classification"
                ] in {
                    "client_error",
                    "server_error",
                    "request_error",
                }:

                    stats[
                        "broken_links"
                    ] += 1

                if link_result[
                    "redirected"
                ]:

                    stats[
                        "redirects"
                    ] += 1

            # --------------------------------------------------
            # PAGE COMPLETED
            # --------------------------------------------------

            stats[
                "pages_crawled"
            ] += 1

            pages.append(
                page
            )

        # --------------------------------------------------
        # FINAL STATISTICS
        # --------------------------------------------------

        stats[
            "pages_discovered"
        ] = len(queued)

        stats[
            "pages_crawled"
        ] = len(pages)

        # --------------------------------------------------
        # RETURN RESULT
        # --------------------------------------------------

        stats["requests_used"] = self._request_count
        stats["runtime_seconds"] = round(time.monotonic() - crawl_started, 3)
        stats["renders_used"] = self._rendered_page_count

        return {
            "pages": pages,

            "robots": robots.to_dict(),

            "sitemaps": {
                "sitemaps_checked": (
                    stats[
                        "sitemaps_checked"
                    ]
                ),

                "urls_discovered": (
                    stats[
                        "sitemap_urls_discovered"
                    ]
                ),

                "details": (
                    sitemap_checker
                    .sitemap_results
                ),
            },

            "stats": stats,

            "pages_discovered": (
                stats[
                    "pages_discovered"
                ]
            ),

            "pages_crawled": (
                stats[
                    "pages_crawled"
                ]
            ),

            "links_checked": (
                stats[
                    "links_checked"
                ]
            ),

            "broken_links": (
                stats[
                    "broken_links"
                ]
            ),

            "redirects": (
                stats[
                    "redirects"
                ]
            ),
        }