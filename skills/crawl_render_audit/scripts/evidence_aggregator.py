from collections import Counter


from .url_utils import normalize_url


class TechnicalEvidenceAggregator:

    def _same_url(self, first, second):
        if not first or not second:
            return False

        return normalize_url(first) == normalize_url(second)

    def _extract_sitemap_urls(self, crawl_result):
        sitemap_urls = set()

        if not crawl_result:
            return sitemap_urls

        sitemaps = crawl_result.get(
            "sitemaps",
            {}
        )

        details = sitemaps.get(
            "details",
            []
        )

        if isinstance(details, dict):
            details = list(
                details.values()
            )

        for detail in details:

            if not isinstance(detail, dict):
                continue

            urls = detail.get(
                "urls",
                []
            )

            for url in urls:

                normalized = normalize_url(
                    url
                )

                if normalized:
                    sitemap_urls.add(
                        normalized
                    )

        return sitemap_urls

    def aggregate(
        self,
        pages,
        crawl_result=None
    ):

        total_pages = len(pages)

        metadata_counts = Counter()
        canonical_counts = Counter()

        jsonld_pages_with_data = 0
        jsonld_pages_without_data = 0

        render_successes = 0
        render_failures = 0

        meaningful_render_changes = 0

        pages_with_multiple_h1 = 0
        pages_without_h1 = 0

        pages_with_missing_title = 0
        pages_with_missing_description = 0

        # --------------------------------------------------
        # CRAWL DEPTH
        # --------------------------------------------------

        depth_counts = Counter()

        # --------------------------------------------------
        # PAGE REDIRECTS
        # --------------------------------------------------

        pages_with_redirects = 0

        # --------------------------------------------------
        # CRAWLED URLS
        # --------------------------------------------------

        crawled_urls = set()

        for page in pages:

            normalized_page_url = (
                normalize_url(
                    page.url
                )
            )

            if normalized_page_url:

                crawled_urls.add(
                    normalized_page_url
                )

            depth_counts[
                page.depth
            ] += 1

            if page.redirect_chain:
                pages_with_redirects += 1

            evidence = getattr(
                page,
                "technical_evidence",
                {},
            )

            # --------------------------------------------------
            # METADATA
            # --------------------------------------------------

            metadata = evidence.get(
                "metadata",
                [],
            )

            for check in metadata:

                check_name = check.get(
                    "check"
                )

                status = check.get(
                    "status"
                )

                if check_name and status:

                    metadata_counts[
                        f"{check_name}:{status}"
                    ] += 1

                if (
                    check_name == "title"
                    and status == "missing"
                ):

                    pages_with_missing_title += 1

                if (
                    check_name == "meta_description"
                    and status == "missing"
                ):

                    pages_with_missing_description += 1

                if (
                    check_name == "h1"
                    and status == "multiple"
                ):

                    pages_with_multiple_h1 += 1

                if (
                    check_name == "h1"
                    and status == "missing"
                ):

                    pages_without_h1 += 1

            # --------------------------------------------------
            # CANONICAL
            # --------------------------------------------------

            canonical = evidence.get(
                "canonical"
            )

            if canonical:

                status = canonical.get(
                    "status"
                )

                if status:

                    canonical_counts[
                        status
                    ] += 1

            # --------------------------------------------------
            # JSON-LD
            # --------------------------------------------------

            jsonld = evidence.get(
                "json_ld"
            )

            if jsonld:

                status = jsonld.get(
                    "status"
                )

                if status == "present":

                    jsonld_pages_with_data += 1

                elif status == "missing":

                    jsonld_pages_without_data += 1

            # --------------------------------------------------
            # RENDERING
            # --------------------------------------------------

            render = evidence.get(
                "render"
            )

            if render:

                status = render.get(
                    "status"
                )

                if status == "success":

                    render_successes += 1

                elif status == "error":

                    render_failures += 1

            # --------------------------------------------------
            # RAW VS RENDERED
            # --------------------------------------------------

            render_diff = evidence.get(
                "raw_vs_rendered"
            )

            if render_diff:

                if render_diff.get(
                    "status"
                ) == "rendered_content_added":

                    meaningful_render_changes += 1

        # --------------------------------------------------
        # LINK STATISTICS
        # --------------------------------------------------

        links_checked = 0
        broken_links = 0
        redirected_links = 0

        if crawl_result:

            links_checked = crawl_result.get(
                "links_checked",
                0,
            )

            broken_links = crawl_result.get(
                "broken_links",
                0,
            )

            redirected_links = crawl_result.get(
                "redirects",
                0,
            )

        # --------------------------------------------------
        # SITEMAP VS CRAWL
        # --------------------------------------------------

        sitemap_urls = (
            self._extract_sitemap_urls(
                crawl_result
            )
        )

        sitemap_urls_crawled = (
            sitemap_urls.intersection(
                crawled_urls
            )
        )

        sitemap_urls_not_crawled = (
            sitemap_urls.difference(
                crawled_urls
            )
        )

        sitemap_coverage = 0.0

        if sitemap_urls:

            sitemap_coverage = round(
                (
                    len(
                        sitemap_urls_crawled
                    )
                    / len(sitemap_urls)
                )
                * 100,
                2,
            )

        # --------------------------------------------------
        # SITEMAP STATISTICS
        # --------------------------------------------------

        sitemaps_checked = 0
        sitemap_urls_discovered = 0

        if crawl_result:

            sitemaps = crawl_result.get(
                "sitemaps",
                {}
            )

            sitemaps_checked = sitemaps.get(
                "sitemaps_checked",
                0,
            )

            sitemap_urls_discovered = sitemaps.get(
                "urls_discovered",
                0,
            )

        return {

            "pages_checked": total_pages,

            # --------------------------------------------------
            # CRAWLABILITY
            # --------------------------------------------------

            "crawlability": {

                "crawl_depth": {
                    f"depth_{depth}": count
                    for depth, count
                    in sorted(
                        depth_counts.items()
                    )
                },

                "pages_with_redirects": (
                    pages_with_redirects
                ),

                "links": {

                    "checked": links_checked,

                    "broken": broken_links,

                    "redirected": (
                        redirected_links
                    ),
                },

                "sitemap": {

                    "sitemaps_checked": (
                        sitemaps_checked
                    ),

                    "urls_discovered": (
                        sitemap_urls_discovered
                    ),

                    "urls_in_sitemap": (
                        len(sitemap_urls)
                    ),

                    "urls_crawled": (
                        len(
                            sitemap_urls_crawled
                        )
                    ),

                    "urls_not_crawled": (
                        len(
                            sitemap_urls_not_crawled
                        )
                    ),

                    "coverage_percent": (
                        sitemap_coverage
                    ),
                },
            },

            # --------------------------------------------------
            # METADATA
            # --------------------------------------------------

            "metadata": {

                "missing_titles": (
                    pages_with_missing_title
                ),

                "missing_descriptions": (
                    pages_with_missing_description
                ),

                "multiple_h1_pages": (
                    pages_with_multiple_h1
                ),

                "missing_h1_pages": (
                    pages_without_h1
                ),

                "status_counts": dict(
                    metadata_counts
                ),
            },

            # --------------------------------------------------
            # CANONICAL
            # --------------------------------------------------

            "canonical": {

                "missing": canonical_counts.get(
                    "missing",
                    0,
                ),

                "invalid": canonical_counts.get(
                    "invalid",
                    0,
                ),

                "cross_domain": canonical_counts.get(
                    "cross_domain",
                    0,
                ),

                "self_referencing": canonical_counts.get(
                    "self_referencing",
                    0,
                ),

                "points_elsewhere": canonical_counts.get(
                    "points_elsewhere",
                    0,
                ),

                "status_counts": dict(
                    canonical_counts
                ),
            },

            # --------------------------------------------------
            # STRUCTURED DATA
            # --------------------------------------------------

            "json_ld": {

                "pages_with_json_ld": (
                    jsonld_pages_with_data
                ),

                "pages_without_json_ld": (
                    jsonld_pages_without_data
                ),
            },

            # --------------------------------------------------
            # RENDERING
            # --------------------------------------------------

            "rendering": {

                "pages_rendered": (
                    render_successes
                    + render_failures
                ),

                "render_successes": (
                    render_successes
                ),

                "render_failures": (
                    render_failures
                ),

                "meaningful_render_changes": (
                    meaningful_render_changes
                ),
            },
        }