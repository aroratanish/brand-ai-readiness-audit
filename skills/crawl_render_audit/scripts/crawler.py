import sys
from collections import deque

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


class WebsiteCrawler:

    def __init__(
        self,
        max_pages: int = 30,
        max_depth: int = 3,
    ):

        self.max_pages = max_pages
        self.max_depth = max_depth

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

    def crawl(
        self,
        start_url: str
    ):

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
        standard_sitemap = normalize_url(
            f"https://{base_hostname}/sitemap.xml"
        )

        if standard_sitemap not in sitemap_candidates:

            sitemap_candidates.append(
                standard_sitemap
            )

        # Also try sitemap_index.xml
        sitemap_index = normalize_url(
            f"https://{base_hostname}/sitemap_index.xml"
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

            current_url, depth = (
                queue.popleft()
            )

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
            # BROWSER RENDERING
            # --------------------------------------------------

            render_url = (
                page.final_url
                or page.url
            )

            render_result = (
                self.renderer.render(
                    render_url
                )
            )

            # --------------------------------------------------
            # RENDERING FAILED
            # --------------------------------------------------

            if render_result.error:

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

            else:

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