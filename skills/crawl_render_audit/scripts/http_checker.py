import requests


DEFAULT_TIMEOUT = 10

USER_AGENT = (
    "BrandAIReadinessAudit/1.0 "
    "(read-only website audit)"
)


class HTTPClient:

    def __init__(self):
        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": (
                    "text/html,"
                    "application/xhtml+xml,"
                    "application/xml;q=0.9,"
                    "*/*;q=0.8"
                ),
            }
        )

    def fetch(
        self,
        url: str,
        timeout: int = DEFAULT_TIMEOUT
    ):

        try:

            response = self.session.get(
                url,
                timeout=timeout,
                allow_redirects=True,
            )

            redirect_chain = [
                history.url
                for history in response.history
            ]

            if response.history:
                redirect_chain.append(
                    response.url
                )

            content_type = (
                response.headers.get(
                    "Content-Type",
                    ""
                )
                .lower()
            )

            is_html = (
                "text/html" in content_type
                or "application/xhtml+xml"
                in content_type
            )

            return {
                "success": True,
                "status_code": response.status_code,
                "requested_url": url,
                "final_url": response.url,
                "redirected": bool(
                    response.history
                ),
                "redirect_chain": redirect_chain,
                "content_type": content_type,
                "is_html": is_html,
                "html": (
                    response.text
                    if is_html
                    else ""
                ),
                "headers": dict(
                    response.headers
                ),
                "error": None,
            }

        except requests.RequestException as exc:

            return {
                "success": False,
                "status_code": None,
                "requested_url": url,
                "final_url": None,
                "redirected": False,
                "redirect_chain": [],
                "content_type": "",
                "is_html": False,
                "html": "",
                "headers": {},
                "error": str(exc),
            }