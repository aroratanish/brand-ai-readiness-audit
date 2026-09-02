from urllib.parse import urlparse, urlunparse, urljoin


def normalize_url(url: str) -> str:
    parsed = urlparse(url)

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    path = parsed.path or "/"

    if path != "/":
        path = path.rstrip("/")

    return urlunparse(
        (
            scheme,
            netloc,
            path,
            "",
            parsed.query,
            "",
        )
    )


def make_absolute_url(base_url: str, link: str) -> str:
    return normalize_url(urljoin(base_url, link))


def get_domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def is_http_url(url: str) -> bool:
    return urlparse(url).scheme in {"http", "https"}

def is_same_domain(url: str, base_domain: str) -> bool:
    return get_domain(url) == base_domain