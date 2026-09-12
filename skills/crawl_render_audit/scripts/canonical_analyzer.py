from .url_utils import normalize_url


class CanonicalAnalyzer:
    """
    Deterministic canonical URL analyzer.

    Reports observed canonical behavior without assigning severity.
    """

    def _evidence(
        self,
        page_url,
        canonical,
        source="raw_html",
        confidence="high",
        **extra,
    ):
        evidence = {
            "page_url": page_url,
            "observed_canonical": canonical,
            "source": source,
            "confidence": confidence,
        }

        evidence.update(extra)

        return evidence

    def analyze(
        self,
        page_url,
        canonical,
    ):
        if not canonical:
            return {
                "status": "missing",
                "evidence": self._evidence(
                    page_url,
                    None,
                ),
            }

        normalized_page = normalize_url(page_url)
        normalized_canonical = normalize_url(canonical)

        if not normalized_canonical:
            return {
                "status": "invalid",
                "evidence": self._evidence(
                    page_url,
                    canonical,
                    normalized_canonical=None,
                ),
            }

        page_host = (
            normalized_page.split("/")[2]
            if normalized_page and "://" in normalized_page
            else None
        )

        canonical_host = (
            normalized_canonical.split("/")[2]
            if "://" in normalized_canonical
            else None
        )

        if page_host and canonical_host and page_host != canonical_host:
            return {
                "status": "cross_domain",
                "evidence": self._evidence(
                    page_url,
                    canonical,
                    normalized_page_url=normalized_page,
                    normalized_canonical_url=normalized_canonical,
                    page_host=page_host,
                    canonical_host=canonical_host,
                ),
            }

        if normalized_page == normalized_canonical:
            return {
                "status": "self_referencing",
                "evidence": self._evidence(
                    page_url,
                    canonical,
                    normalized_page_url=normalized_page,
                    normalized_canonical_url=normalized_canonical,
                ),
            }

        return {
            "status": "points_elsewhere",
            "evidence": self._evidence(
                page_url,
                canonical,
                normalized_page_url=normalized_page,
                normalized_canonical_url=normalized_canonical,
            ),
        }