from .http_checker import HTTPClient
from .url_utils import normalize_url


class LinkChecker:

    def __init__(self, client=None):

        self.client = (
            client
            if client is not None
            else HTTPClient()
        )

        self.cache = {}

    def check(self, url: str):

        url = normalize_url(url)

        if not url:

            result = {
                "url": url,
                "status_code": None,
                "success": False,
                "final_url": None,
                "redirected": False,
                "redirect_chain": [],
                "content_type": "",
                "classification": "invalid_url",
                "error": "Invalid URL"
            }

            return result

        if url in self.cache:
            return self.cache[url]

        response = self.client.fetch(url)

        result = {
            "url": url,
            "status_code": response[
                "status_code"
            ],
            "success": response[
                "success"
            ],
            "final_url": response[
                "final_url"
            ],
            "redirected": response[
                "redirected"
            ],
            "redirect_chain": response[
                "redirect_chain"
            ],
            "content_type": response[
                "content_type"
            ],
            "classification": self.classify(
                response
            ),
            "error": response[
                "error"
            ]
        }

        self.cache[url] = result

        return result

    def classify(self, response):

        if not response["success"]:
            return "request_error"

        status = response["status_code"]

        if status is None:
            return "request_error"

        if 200 <= status < 300:
            return "ok"

        if 300 <= status < 400:
            return "redirect"

        if 400 <= status < 500:
            return "client_error"

        if 500 <= status < 600:
            return "server_error"

        return "other"