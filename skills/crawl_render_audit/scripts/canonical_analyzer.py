from urllib.parse import urlparse

from .url_utils import normalize_url


class CanonicalAnalyzer:

    def analyze(
        self,
        page_url: str,
        canonical: str | None,
    ):

        if not canonical:

            return {
                "check": "canonical",
                "status": "missing",
                "evidence": {
                    "page_url": page_url,
                    "canonical": None,
                },
            }

        normalized_page = normalize_url(
            page_url
        )

        normalized_canonical = normalize_url(
            canonical
        )

        if not normalized_canonical:

            return {
                "check": "canonical",
                "status": "invalid",
                "evidence": {
                    "page_url": page_url,
                    "canonical": canonical,
                },
            }

        page_host = (
            urlparse(
                normalized_page
            ).hostname
            or ""
        ).lower()

        canonical_host = (
            urlparse(
                normalized_canonical
            ).hostname
            or ""
        ).lower()

        if page_host != canonical_host:

            return {
                "check": "canonical",
                "status": "cross_domain",
                "evidence": {
                    "page_url": page_url,
                    "canonical": normalized_canonical,
                    "page_hostname": page_host,
                    "canonical_hostname": canonical_host,
                },
            }

        if (
            normalized_page
            == normalized_canonical
        ):

            return {
                "check": "canonical",
                "status": "self_referencing",
                "evidence": {
                    "page_url": normalized_page,
                    "canonical": normalized_canonical,
                },
            }

        return {
            "check": "canonical",
            "status": "points_elsewhere",
            "evidence": {
                "page_url": normalized_page,
                "canonical": normalized_canonical,
            },
        }