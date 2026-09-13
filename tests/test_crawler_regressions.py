import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from skills.crawl_render_audit.scripts.crawler import WebsiteCrawler
from skills.crawl_render_audit.scripts.http_checker import HTTPClient
from skills.crawl_render_audit.scripts.html_parser import parse_html
from skills.crawl_render_audit.scripts.renderer import RenderResult
from skills.crawl_render_audit.scripts.url_utils import normalize_url


class CrawlerRegressionTests(unittest.TestCase):

    def test_url_normalization_removes_tracking_and_default_port(self):
        self.assertEqual(
            normalize_url("HTTPS://Example.com:443/path/?utm_source=x&ok=1#section"),
            "https://example.com/path?ok=1",
        )

    def test_html_parser_classifies_internal_external_links(self):
        parsed = parse_html(
            '<a href="/about">About</a><a href="https://other.test/x">Other</a>',
            "https://example.com/",
        )
        self.assertEqual(parsed["internal_links"], ["https://example.com/about"])
        self.assertEqual(parsed["external_links"], ["https://other.test/x"])

    def test_html_parser_reads_valid_and_malformed_json_ld(self):
        parsed = parse_html(
            """
            <script type="application/ld+json">{"@type":"Article"}</script>
            <script type="application/ld+json">{not valid json}</script>
            """,
            "https://example.com/",
        )
        self.assertEqual(parsed["json_ld"][0]["@type"], "Article")
        self.assertTrue(parsed["json_ld"][1]["_parse_error"])

    def test_http_client_marks_http_errors_failed(self):
        response = Mock(
            status_code=404,
            url="https://example.com/missing",
            history=[],
            headers={"Content-Type": "text/html"},
            text="missing",
        )
        client = HTTPClient()
        client.session.get = Mock(return_value=response)

        result = client.fetch("https://example.com/missing")

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 404)
        self.assertEqual(result["error"], "HTTP 404")

    def test_http_client_preserves_redirect_success(self):
        history = [SimpleNamespace(url="https://example.com/old")]
        response = Mock(
            status_code=200,
            url="https://example.com/new",
            history=history,
            headers={"Content-Type": "text/html"},
            text="ok",
        )
        client = HTTPClient()
        client.session.get = Mock(return_value=response)

        result = client.fetch("https://example.com/old")

        self.assertTrue(result["success"])
        self.assertTrue(result["redirected"])
        self.assertEqual(result["redirect_chain"], [
            "https://example.com/old",
            "https://example.com/new",
        ])

    def test_crawler_respects_page_limit(self):
        html = {
            "https://example.com/": '<a href="/one">one</a><a href="/two">two</a>',
            "https://example.com/one": '<a href="/nested">nested</a>',
            "https://example.com/two": "<p>two</p>",
            "https://example.com/nested": "<p>nested</p>",
        }

        def fetch(url):
            return {
                "success": True,
                "status_code": 200,
                "requested_url": url,
                "final_url": url,
                "redirected": False,
                "redirect_chain": [],
                "content_type": "text/html",
                "is_html": True,
                "html": html[url],
                "headers": {},
                "error": None,
            }

        robots = Mock()
        robots.sitemaps = []
        robots.can_fetch.return_value = True
        robots.to_dict.return_value = {"exists": False}
        sitemap = Mock()
        sitemap.visited_sitemaps = set()
        sitemap.discovered_urls = set()
        sitemap.max_sitemaps = 2
        sitemap.parse.return_value = {"exists": False}
        renderer = Mock()
        renderer.render.return_value = RenderResult(url="", rendered_html="")
        link_checker = Mock()
        link_checker.check.side_effect = lambda url: {
            "url": url,
            "status_code": 200,
            "success": True,
            "final_url": url,
            "redirected": False,
            "redirect_chain": [],
            "content_type": "text/html",
            "classification": "ok",
            "error": None,
        }

        with patch("skills.crawl_render_audit.scripts.crawler.RobotsPolicy", return_value=robots), \
                patch("skills.crawl_render_audit.scripts.crawler.SitemapChecker", return_value=sitemap):
            crawler = WebsiteCrawler(max_pages=2, max_depth=1)
            crawler.client.fetch = Mock(side_effect=fetch)
            crawler.renderer = renderer
            crawler.link_checker = link_checker
            result = crawler.crawl("https://example.com/")

        self.assertEqual(len(result["pages"]), 2)
        self.assertEqual(result["pages_crawled"], 2)

    def test_crawler_respects_depth_limit(self):
        html = {
            "https://example.com/": '<a href="/one">one</a>',
            "https://example.com/one": '<a href="/nested">nested</a>',
            "https://example.com/nested": "<p>nested</p>",
        }

        def fetch(url):
            return {
                "success": True,
                "status_code": 200,
                "requested_url": url,
                "final_url": url,
                "redirected": False,
                "redirect_chain": [],
                "content_type": "text/html",
                "is_html": True,
                "html": html[url],
                "headers": {},
                "error": None,
            }

        robots = Mock()
        robots.sitemaps = []
        robots.can_fetch.return_value = True
        robots.to_dict.return_value = {"exists": False}
        sitemap = Mock()
        sitemap.visited_sitemaps = set()
        sitemap.discovered_urls = set()
        sitemap.max_sitemaps = 2
        sitemap.parse.return_value = {"exists": False}
        renderer = Mock()
        renderer.render.return_value = RenderResult(url="", rendered_html="")
        link_checker = Mock()
        link_checker.check.side_effect = lambda url: {
            "url": url,
            "status_code": 200,
            "success": True,
            "final_url": url,
            "redirected": False,
            "redirect_chain": [],
            "content_type": "text/html",
            "classification": "ok",
            "error": None,
        }

        with patch("skills.crawl_render_audit.scripts.crawler.RobotsPolicy", return_value=robots), \
                patch("skills.crawl_render_audit.scripts.crawler.SitemapChecker", return_value=sitemap):
            crawler = WebsiteCrawler(max_pages=5, max_depth=0)
            crawler.client.fetch = Mock(side_effect=fetch)
            crawler.renderer = renderer
            crawler.link_checker = link_checker
            result = crawler.crawl("https://example.com/")

        self.assertEqual(len(result["pages"]), 1)
        self.assertEqual(result["pages"][0].depth, 0)
        self.assertEqual(result["pages_crawled"], 1)


if __name__ == "__main__":
    unittest.main()