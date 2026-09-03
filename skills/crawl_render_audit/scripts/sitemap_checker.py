import xml.etree.ElementTree as ET

import requests

from .url_utils import normalize_url


USER_AGENT = "BrandAIReadinessAudit/1.0"

DEFAULT_TIMEOUT = 10

MAX_SITEMAPS = 50

MAX_URLS = 5000


class SitemapChecker:

    def __init__(
        self,
        timeout=DEFAULT_TIMEOUT,
        max_sitemaps=MAX_SITEMAPS,
        max_urls=MAX_URLS,
    ):

        self.timeout = timeout
        self.max_sitemaps = max_sitemaps
        self.max_urls = max_urls

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )

        self.visited_sitemaps = set()
        self.discovered_urls = set()
        self.sitemap_results = []

    def fetch(self, sitemap_url):

        try:

            response = self.session.get(
                sitemap_url,
                timeout=self.timeout,
            )

            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "content": response.text,
                "content_type": response.headers.get(
                    "Content-Type",
                    ""
                ),
                "error": None,
            }

        except requests.RequestException as exc:

            return {
                "success": False,
                "status_code": None,
                "content": "",
                "content_type": "",
                "error": str(exc),
            }

    def parse(self, sitemap_url):

        sitemap_url = normalize_url(
            sitemap_url
        )

        if not sitemap_url:

            return {
                "url": sitemap_url,
                "exists": False,
                "status_code": None,
                "type": None,
                "urls": [],
                "sitemaps": [],
                "error": "Invalid sitemap URL",
            }

        if sitemap_url in self.visited_sitemaps:

            return {
                "url": sitemap_url,
                "exists": True,
                "status_code": 200,
                "type": "duplicate",
                "urls": [],
                "sitemaps": [],
                "error": None,
            }

        if (
            len(self.visited_sitemaps)
            >= self.max_sitemaps
        ):

            return {
                "url": sitemap_url,
                "exists": False,
                "status_code": None,
                "type": None,
                "urls": [],
                "sitemaps": [],
                "error": "Maximum sitemap limit reached",
            }

        self.visited_sitemaps.add(
            sitemap_url
        )

        data = self.fetch(
            sitemap_url
        )

        result = {
            "url": sitemap_url,
            "exists": data["success"],
            "status_code": data["status_code"],
            "type": None,
            "urls": [],
            "sitemaps": [],
            "error": data["error"],
        }

        if not data["success"]:

            self.sitemap_results.append(
                result
            )

            return result

        try:

            root = ET.fromstring(
                data["content"]
            )

        except ET.ParseError as exc:

            result["error"] = (
                f"Invalid XML: {exc}"
            )

            self.sitemap_results.append(
                result
            )

            return result

        root_tag = self._strip_namespace(
            root.tag
        )

        if root_tag == "urlset":

            result["type"] = "urlset"

            for url_element in root:

                if (
                    len(self.discovered_urls)
                    >= self.max_urls
                ):
                    break

                url = self._get_loc(
                    url_element
                )

                if not url:
                    continue

                url = normalize_url(
                    url
                )

                if not url:
                    continue

                if url in self.discovered_urls:
                    continue

                self.discovered_urls.add(
                    url
                )

                result["urls"].append(
                    url
                )

        elif root_tag == "sitemapindex":

            result["type"] = "sitemapindex"

            for sitemap_element in root:

                sitemap_url = self._get_loc(
                    sitemap_element
                )

                if not sitemap_url:
                    continue

                sitemap_url = normalize_url(
                    sitemap_url
                )

                if not sitemap_url:
                    continue

                if sitemap_url in (
                    result["sitemaps"]
                ):
                    continue

                result["sitemaps"].append(
                    sitemap_url
                )

        else:

            result["error"] = (
                "Unknown sitemap XML type"
            )

        self.sitemap_results.append(
            result
        )

        return result

    def discover(self, sitemap_urls):

        queue = []

        for sitemap_url in sitemap_urls:

            sitemap_url = normalize_url(
                sitemap_url
            )

            if sitemap_url:
                queue.append(
                    sitemap_url
                )

        while (
            queue
            and len(
                self.visited_sitemaps
            ) < self.max_sitemaps
            and len(
                self.discovered_urls
            ) < self.max_urls
        ):

            current = queue.pop(0)

            if current in (
                self.visited_sitemaps
            ):
                continue

            result = self.parse(
                current
            )

            for child in result[
                "sitemaps"
            ]:

                if child not in (
                    self.visited_sitemaps
                ):

                    queue.append(
                        child
                    )

        return {
            "sitemaps_checked": len(
                self.visited_sitemaps
            ),
            "urls_discovered": len(
                self.discovered_urls
            ),
            "urls": sorted(
                self.discovered_urls
            ),
            "sitemaps": self.sitemap_results,
        }

    @staticmethod
    def _strip_namespace(tag):

        if "}" in tag:

            return tag.split(
                "}",
                1
            )[1].lower()

        return tag.lower()

    @classmethod
    def _get_loc(
        cls,
        element
    ):

        for child in element:

            if (
                cls._strip_namespace(
                    child.tag
                )
                == "loc"
            ):

                if child.text:

                    return child.text.strip()

        return None


def parse_sitemap(
    sitemap_url
):

    checker = SitemapChecker()

    result = checker.parse(
        sitemap_url
    )

    if result["type"] == "sitemapindex":

        discovered = checker.discover(
            result["sitemaps"]
        )

        result["urls"] = discovered[
            "urls"
        ]

        result[
            "sitemaps_checked"
        ] = discovered[
            "sitemaps_checked"
        ]

        result[
            "nested_sitemaps"
        ] = discovered[
            "sitemaps"
        ]

    else:

        result[
            "sitemaps_checked"
        ] = len(
            checker.visited_sitemaps
        )

        result[
            "nested_sitemaps"
        ] = checker.sitemap_results

    return result