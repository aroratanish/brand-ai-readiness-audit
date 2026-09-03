from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

from .http_checker import HTTPClient


USER_AGENT = "BrandAIReadinessAudit"
class RobotsPolicy:

    def __init__(
        self,
        site_url: str,
        client: HTTPClient | None = None
    ):

        self.site_url = site_url
        self.robots_url = urljoin(
            site_url,
            "/robots.txt"
        )

        self.client = (
            client
            if client is not None
            else HTTPClient()
        )

        self.parser = RobotFileParser()

        self.exists = False
        self.status_code = None
        self.error = None
        self.sitemaps = []

        self.disallowed_paths = []
        self.allowed_paths = []

        self._load()

    def _load(self):

        try:

            response = self.client.fetch(
                self.robots_url
            )

            self.status_code = (
                response["status_code"]
            )

            if (
                response["success"]
                and response["status_code"] == 200
            ):

                self.exists = True

                content = response.get(
                    "html",
                    ""
                )

                # robots.txt is plain text,
                # so use a direct requests session
                raw_response = self.client.session.get(
                    self.robots_url,
                    timeout=10
                )

                content = raw_response.text

                self.parser.set_url(
                    self.robots_url
                )

                self.parser.parse(
                    content.splitlines()
                )

                self._extract_metadata(
                    content
                )

        except Exception as exc:

            self.error = str(exc)

    def _extract_metadata(
        self,
        content: str
    ):
        for line in content.splitlines():

            line = line.strip()

            if not line:
                continue

            lower = line.lower()

            if lower.startswith(
                "sitemap:"
            ):

                sitemap = line.split(
                    ":",
                    1
                )[1].strip()

                if sitemap:
                    self.sitemaps.append(
                        sitemap
                    )

            elif lower.startswith(
                "disallow:"
            ):

                path = line.split(
                    ":",
                    1
                )[1].strip()

                if path:
                    self.disallowed_paths.append(
                        path
                    )

            elif lower.startswith(
                "allow:"
            ):

                path = line.split(
                    ":",
                    1
                )[1].strip()

                if path:
                    self.allowed_paths.append(
                        path
                    )

    def can_fetch(
        self,
        url: str
    ) -> bool:

        # If robots.txt doesn't exist,
        # crawling is allowed.
        if not self.exists:
            return True

        return self.parser.can_fetch(
            USER_AGENT,
            url
        )

    def to_dict(self):

        return {
            "url": self.robots_url,
            "exists": self.exists,
            "status_code": self.status_code,
            "sitemaps": list(
                dict.fromkeys(
                    self.sitemaps
                )
            ),
            "disallowed_paths": list(
                dict.fromkeys(
                    self.disallowed_paths
                )
            ),
            "allowed_paths": list(
                dict.fromkeys(
                    self.allowed_paths
                )
            ),
            "error": self.error,
        }


