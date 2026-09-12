from collections import Counter


class CrossSignalAnalyzer:
    """
    Correlates deterministic technical signals across a crawled page.

    This analyzer does not assign severity or make recommendations.
    It produces factual relationships that can be consumed by the
    reasoning layer.
    """

    def _get_render_diff(self, page):
        evidence = getattr(page, "technical_evidence", {}) or {}
        return evidence.get("raw_vs_rendered") or {}

    def _get_render(self, page):
        evidence = getattr(page, "technical_evidence", {}) or {}
        return evidence.get("render") or {}

    def _get_json_ld(self, page):
        evidence = getattr(page, "technical_evidence", {}) or {}
        return evidence.get("json_ld") or {}

    def _get_metadata(self, page):
        evidence = getattr(page, "technical_evidence", {}) or {}
        return evidence.get("metadata") or []

    def _metadata_status(self, metadata, check_name):
        for check in metadata:
            if check.get("check") == check_name:
                return check.get("status")
        return None

    def _raw_content_dependency(self, render_diff):
        """
        Determine whether meaningful page content appears only after
        rendering.

        This is a factual classification, not a severity judgment.
        """

        status = render_diff.get("status")

        if status == "rendered_content_added":
            return "meaningful_rendered_content_added"

        if status == "rendered_content_reduced":
            return "rendered_content_reduced"

        if status == "minor_rendered_change":
            return "minor_render_change"

        if status == "no_meaningful_change":
            return "no_meaningful_render_change"

        return "unknown"

    def analyze_page(self, page):
        """
        Produce cross-signal evidence for one page.
        """

        render_diff = self._get_render_diff(page)
        render = self._get_render(page)
        json_ld = self._get_json_ld(page)
        metadata = self._get_metadata(page)

        signals = []

        # ---------------------------------------------------------
        # Signal 1: Raw HTML vs rendered content
        # ---------------------------------------------------------

        raw_render_relationship = self._raw_content_dependency(
            render_diff
        )

        if (
            raw_render_relationship
            == "meaningful_rendered_content_added"
        ):
            signals.append(
                {
                    "signal": "rendered_content_dependency",
                    "status": "present",
                    "evidence": {
                        "relationship": (
                            "meaningful_content_added_after_render"
                        ),
                        "render_status": render.get("status"),
                        "raw_vs_rendered_status": (
                            render_diff.get("status")
                        ),
                        "raw_text_length": render_diff.get(
                            "evidence",
                            {},
                        ).get("raw_text_length"),
                        "rendered_text_length": render_diff.get(
                            "evidence",
                            {},
                        ).get("rendered_text_length"),
                        "text_delta": render_diff.get(
                            "evidence",
                            {},
                        ).get("text_delta"),
                        "text_delta_ratio": render_diff.get(
                            "evidence",
                            {},
                        ).get("text_delta_ratio"),
                    },
                }
            )

        # ---------------------------------------------------------
        # Signal 2: Structured data + rendered content
        # ---------------------------------------------------------

        jsonld_status = json_ld.get("status")

        if jsonld_status == "present":
            jsonld_relationship = "structured_data_present"

        elif jsonld_status == "missing":
            jsonld_relationship = "structured_data_missing"

        else:
            jsonld_relationship = "structured_data_unknown"

        if render_diff.get("status") == "rendered_content_added":
            signals.append(
                {
                    "signal": "structured_data_render_relationship",
                    "status": "correlated",
                    "evidence": {
                        "structured_data": jsonld_relationship,
                        "rendered_content_added": True,
                        "json_ld_types": (
                            json_ld.get("evidence", {})
                            .get("types", [])
                        ),
                    },
                }
            )

        # ---------------------------------------------------------
        # Signal 3: Structured data + page metadata
        # ---------------------------------------------------------

        title_status = self._metadata_status(
            metadata,
            "title",
        )

        h1_status = self._metadata_status(
            metadata,
            "h1",
        )

        if jsonld_status == "present":
            signals.append(
                {
                    "signal": "structured_data_metadata_relationship",
                    "status": "correlated",
                    "evidence": {
                        "json_ld_present": True,
                        "json_ld_types": (
                            json_ld.get("evidence", {})
                            .get("types", [])
                        ),
                        "title_status": title_status,
                        "h1_status": h1_status,
                    },
                }
            )

        # ---------------------------------------------------------
        # Signal 4: Render failure + raw content
        # ---------------------------------------------------------

        if render.get("status") == "error":
            raw_html = getattr(page, "raw_html", "") or ""

            signals.append(
                {
                    "signal": "render_failure_raw_fallback",
                    "status": "correlated",
                    "evidence": {
                        "render_status": "error",
                        "raw_html_available": bool(raw_html),
                        "raw_html_length": len(raw_html),
                    },
                }
            )

        # ---------------------------------------------------------
        # Signal 5: Redirect + canonical
        # ---------------------------------------------------------

        canonical = (
            getattr(page, "technical_evidence", {}) or {}
        ).get("canonical") or {}

        if page.redirect_chain and canonical:
            signals.append(
                {
                    "signal": "redirect_canonical_relationship",
                    "status": "correlated",
                    "evidence": {
                        "redirected": True,
                        "redirect_chain_length": len(
                            page.redirect_chain
                        ),
                        "canonical_status": canonical.get(
                            "status"
                        ),
                        "canonical_target": canonical.get(
                            "evidence",
                            {},
                        ).get("canonical"),
                    },
                }
            )

        # ---------------------------------------------------------
        # Signal 6: Missing H1 + missing title
        # ---------------------------------------------------------

        if (
            title_status == "missing"
            and h1_status == "missing"
        ):
            signals.append(
                {
                    "signal": "core_metadata_gap",
                    "status": "correlated",
                    "evidence": {
                        "title_status": title_status,
                        "h1_status": h1_status,
                    },
                }
            )

        return {
            "url": page.url,
            "signals": signals,
            "signal_count": len(signals),
        }

    def analyze_site(self, pages):
        """
        Produce page-level and site-level cross-signal evidence.
        """

        page_results = []

        signal_counts = Counter()

        for page in pages:
            result = self.analyze_page(page)
            page_results.append(result)

            for signal in result["signals"]:
                signal_name = signal.get("signal")

                if signal_name:
                    signal_counts[signal_name] += 1

        return {
            "pages_analyzed": len(pages),
            "pages_with_cross_signals": sum(
                1
                for result in page_results
                if result["signal_count"] > 0
            ),
            "signal_counts": dict(signal_counts),
            "pages": page_results,
        }