from urllib.parse import urlparse, urlunparse, urljoin


TRACKING_PARAMETERS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
}


def normalize_url(url: str) -> str:
    if not url:
        return ""

    parsed = urlparse(url)

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    if not scheme or not netloc:
        return ""

    # Remove default ports
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]

    if scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]

    path = parsed.path or "/"

    if path != "/":
        path = path.rstrip("/")

    # Remove fragments and common tracking parameters
    query_parts = []

    if parsed.query:
        for part in parsed.query.split("&"):
            if "=" in part:
                key, value = part.split("=", 1)
            else:
                key, value = part, ""

            if key.lower() not in TRACKING_PARAMETERS:
                query_parts.append(
                    f"{key}={value}"
                )

    query = "&".join(query_parts)

    return urlunparse(
        (
            scheme,
            netloc,
            path,
            "",
            query,
            "",
        )
    )


def make_absolute_url(
    base_url: str,
    link: str
) -> str:

    if not link:
        return ""

    return normalize_url(
        urljoin(base_url, link)
    )


def get_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower()


def get_hostname(url: str) -> str:
    parsed = urlparse(url)
    return (parsed.hostname or "").lower()


def is_http_url(url: str) -> bool:
    return urlparse(url).scheme in {
        "http",
        "https",
    }


def is_same_domain(
    url: str,
    base_url: str
) -> bool:

    return (
        get_hostname(url)
        == get_hostname(base_url)
    )