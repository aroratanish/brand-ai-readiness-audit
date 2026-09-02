import requests


DEFAULT_TIMEOUT = 10


def fetch_page(url: str, timeout: int = DEFAULT_TIMEOUT):
    try:
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={
                "User-Agent": (
                    "BrandAIReadinessAudit/1.0 "
                    "(read-only website audit)"
                )
            },
        )

        return {
            "success": True,
            "status_code": response.status_code,
            "final_url": response.url,
            "redirect_chain": [
                history.url
                for history in response.history
            ] + [response.url],
            "html": response.text,
            "headers": dict(response.headers),
            "error": None,
        }

    except requests.RequestException as exc:
        return {
            "success": False,
            "status_code": None,
            "final_url": None,
            "redirect_chain": [],
            "html": "",
            "headers": {},
            "error": str(exc),
        }