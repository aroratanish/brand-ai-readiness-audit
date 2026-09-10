from collections import Counter

from .url_utils import normalize_url


class TechnicalEvidenceAggregator:
    """
    Aggregates page-level technical checks into site-level evidence.

    This layer reports audit scope and coverage explicitly so downstream
    reasoning can distinguish between:
      - what was actually checked,
      - what was discovered,
      - and what remained outside the crawl.
    """

    def _extract_sitemap_urls(self, crawl_result):
        sitemap_urls = set()

        if not crawl_result:
            return sitemap_urls

        sitemaps = crawl_result.get("sitemaps", {})
        details = sitemaps.get("details", [])

        if isinstance(details, dict):
            details = list(details.values())

        for detail in details:
            if not isinstance(detail, dict):
                continue

            urls = detail.get("urls", [])

            for url in urls:
                normalized = normalize_url(url)

                if normalized:
                    sitemap_urls.add(normalized)

        return sitemap_urls

    def _rate(self, count, total):
        """
        Return a percentage rounded to two decimal places.

        Returns 0.0 when the denominator is zero.
        """
        if not total:
            return 0.0

        return round((count / total) * 100, 2)

    def aggregate(self, pages, crawl_result=None):
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

        depth_counts = Counter()

        pages_with_redirects = 0

        crawled_urls = set()

        # ---------------------------------------------------------
        # Crawl configuration / scope
        # ---------------------------------------------------------

        pages_discovered = 0
        max_pages = None
        max_depth = None

        if crawl_result:
            pages_discovered = crawl_result.get(
                "pages_discovered",
                total_pages,
            )

            max_pages = crawl_result.get("max_pages")

            max_depth = crawl_result.get("max_depth")

        # Some crawler implementations may not expose limits directly.
        # Keep the fields nullable rather than inventing values.
        crawl_limit_reached = False

        if max_pages is not None:
            crawl_limit_reached = total_pages >= max_pages

        # ---------------------------------------------------------
        # Page-level evidence
        # ---------------------------------------------------------

        for page in pages:
            normalized_page_url = normalize_url(page.url)

            if normalized_page_url:
                crawled_urls.add(normalized_page_url)

            depth_counts[page.depth] += 1

            if page.redirect_chain:
                pages_with_redirects += 1

            evidence = getattr(page, "technical_evidence", {})

            # -------------------------
            # Metadata
            # -------------------------

            metadata = evidence.get("metadata", [])

            for check in metadata:
                check_name = check.get("check")
                status = check.get("status")

                if check_name and status:
                    metadata_counts[
                        f"{check_name}:{status}"
                    ] += 1

                if check_name == "title" and status == "missing":
                    pages_with_missing_title += 1

                if (
                    check_name == "meta_description"
                    and status == "missing"
                ):
                    pages_with_missing_description += 1

                if check_name == "h1" and status == "multiple":
                    pages_with_multiple_h1 += 1

                if check_name == "h1" and status == "missing":
                    pages_without_h1 += 1

            # -------------------------
            # Canonical
            # -------------------------

            canonical = evidence.get("canonical")

            if canonical:
                status = canonical.get("status")

                if status:
                    canonical_counts[status] += 1

            # -------------------------
            # JSON-LD
            # -------------------------

            jsonld = evidence.get("json_ld")

            if jsonld:
                status = jsonld.get("status")

                if status == "present":
                    jsonld_pages_with_data += 1

                elif status == "missing":
                    jsonld_pages_without_data += 1

            # -------------------------
            # Rendering
            # -------------------------

            render = evidence.get("render")

            if render:
                status = render.get("status")

                if status == "success":
                    render_successes += 1

                elif status == "error":
                    render_failures += 1

            # -------------------------
            # Raw vs rendered
            # -------------------------

            render_diff = evidence.get("raw_vs_rendered")

            if (
                render_diff
                and render_diff.get("status")
                == "rendered_content_added"
            ):
                meaningful_render_changes += 1

        # ---------------------------------------------------------
        # Link-level evidence
        # ---------------------------------------------------------

        links_checked = 0
        broken_links = 0
        redirected_links = 0

        if crawl_result:
            links_checked = crawl_result.get("links_checked", 0)
            broken_links = crawl_result.get("broken_links", 0)
            redirected_links = crawl_result.get("redirects", 0)

        # ---------------------------------------------------------
        # Sitemap coverage
        # ---------------------------------------------------------

        sitemap_urls = self._extract_sitemap_urls(crawl_result)

        sitemap_urls_crawled = sitemap_urls.intersection(
            crawled_urls
        )

        sitemap_urls_not_crawled = sitemap_urls.difference(
            crawled_urls
        )

        sitemap_coverage = 0.0

        if sitemap_urls:
            sitemap_coverage = self._rate(
                len(sitemap_urls_crawled),
                len(sitemap_urls),
            )

        sitemaps_checked = 0
        sitemap_urls_discovered = 0

        if crawl_result:
            sitemaps = crawl_result.get("sitemaps", {})

            sitemaps_checked = sitemaps.get(
                "sitemaps_checked",
                0,
            )

            sitemap_urls_discovered = sitemaps.get(
                "urls_discovered",
                0,
            )

        # ---------------------------------------------------------
        # Audit scope / coverage
        # ---------------------------------------------------------

        discovered_pages = max(
            pages_discovered,
            total_pages,
        )

        crawl_coverage_percent = self._rate(
            total_pages,
            discovered_pages,
        )

        coverage_basis = "discovered_pages"

        if discovered_pages == total_pages:
            coverage_basis = "crawled_pages"

        # ---------------------------------------------------------
        # Issue rates
        # ---------------------------------------------------------

        missing_title_rate = self._rate(
            pages_with_missing_title,
            total_pages,
        )

        missing_description_rate = self._rate(
            pages_with_missing_description,
            total_pages,
        )

        missing_h1_rate = self._rate(
            pages_without_h1,
            total_pages,
        )

        multiple_h1_rate = self._rate(
            pages_with_multiple_h1,
            total_pages,
        )

        broken_link_rate = self._rate(
            broken_links,
            links_checked,
        )

        redirect_rate = self._rate(
            redirected_links,
            links_checked,
        )

        # ---------------------------------------------------------
        # Return aggregated evidence
        # ---------------------------------------------------------

        return {
            "scope": {
                "pages_checked": total_pages,
                "pages_discovered": discovered_pages,
                "max_pages": max_pages,
                "max_depth": max_depth,
                "crawl_limit_reached": crawl_limit_reached,
                "coverage_percent": crawl_coverage_percent,
                "coverage_basis": coverage_basis,
                "depth_distribution": {
                    f"depth_{depth}": count
                    for depth, count in sorted(
                        depth_counts.items()
                    )
                },
            },

            "crawlability": {
                "crawl_depth": {
                    f"depth_{depth}": count
                    for depth, count in sorted(
                        depth_counts.items()
                    )
                },
                "pages_with_redirects": pages_with_redirects,

                "links": {
                    "checked": links_checked,
                    "broken": broken_links,
                    "redirected": redirected_links,
                    "broken_rate_percent": broken_link_rate,
                    "redirect_rate_percent": redirect_rate,
                },

                "sitemap": {
                    "sitemaps_checked": sitemaps_checked,
                    "urls_discovered": sitemap_urls_discovered,
                    "urls_in_sitemap": len(sitemap_urls),
                    "urls_crawled": len(sitemap_urls_crawled),
                    "urls_not_crawled": len(
                        sitemap_urls_not_crawled
                    ),
                    "coverage_percent": sitemap_coverage,
                },
            },

            "metadata": {
                "missing_titles": pages_with_missing_title,
                "missing_title_rate_percent": missing_title_rate,

                "missing_descriptions": (
                    pages_with_missing_description
                ),
                "missing_description_rate_percent": (
                    missing_description_rate
                ),

                "multiple_h1_pages": pages_with_multiple_h1,
                "multiple_h1_rate_percent": multiple_h1_rate,

                "missing_h1_pages": pages_without_h1,
                "missing_h1_rate_percent": missing_h1_rate,

                "status_counts": dict(metadata_counts),
            },

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
                "status_counts": dict(canonical_counts),
            },

            "json_ld": {
                "pages_with_json_ld": (
                    jsonld_pages_with_data
                ),
                "pages_without_json_ld": (
                    jsonld_pages_without_data
                ),
                "json_ld_presence_rate_percent": self._rate(
                    jsonld_pages_with_data,
                    total_pages,
                ),
            },

            "rendering": {
                "pages_rendered": (
                    render_successes + render_failures
                ),
                "render_successes": render_successes,
                "render_failures": render_failures,
                "render_success_rate_percent": self._rate(
                    render_successes,
                    render_successes + render_failures,
                ),
                "meaningful_render_changes": (
                    meaningful_render_changes
                ),
                "meaningful_render_change_rate_percent": (
                    self._rate(
                        meaningful_render_changes,
                        render_successes,
                    )
                ),
            },
        }