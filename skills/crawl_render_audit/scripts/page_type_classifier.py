import re
from urllib.parse import urlparse


class PageTypeClassifier:
    """
    Deterministically classifies pages using multiple technical signals.

    Signals used:
    - JSON-LD / structured-data types
    - URL path patterns
    - page title
    - H1 headings
    - H2 headings

    This classifier does not assign severity or recommendations.
    """

    PAGE_TYPES = (
        "homepage",
        "product",
        "category",
        "article",
        "documentation",
        "pricing",
        "contact",
        "about",
        "faq",
        "search",
        "login",
        "other",
    )

    def _normalize_text(self, value):
        if not value:
            return ""

        return re.sub(
            r"\s+",
            " ",
            str(value),
        ).strip().lower()

    def _get_jsonld_types(self, page):
        evidence = (
            getattr(page, "technical_evidence", {})
            or {}
        )

        json_ld_evidence = evidence.get(
            "json_ld",
            {},
        )

        types = (
            json_ld_evidence
            .get("evidence", {})
            .get("types", [])
        )

        if types:
            return [
                self._normalize_text(item)
                for item in types
                if item
            ]

        # Fallback to the raw JSON-LD stored on PageResult.
        raw_types = []

        for block in getattr(page, "json_ld", []) or []:
            if not isinstance(block, dict):
                continue

            block_type = block.get("@type")

            if isinstance(block_type, list):
                raw_types.extend(block_type)

            elif block_type:
                raw_types.append(block_type)

        return [
            self._normalize_text(item)
            for item in raw_types
            if item
        ]

    def _get_title(self, page):
        return self._normalize_text(
            getattr(page, "title", "")
        )

    def _get_h1(self, page):
        headings = getattr(page, "h1", []) or []

        return " ".join(
            self._normalize_text(item)
            for item in headings
        )

    def _get_h2(self, page):
        headings = getattr(page, "h2", []) or []

        return " ".join(
            self._normalize_text(item)
            for item in headings
        )

    def _get_path(self, page):
        url = getattr(page, "url", "") or ""

        try:
            return self._normalize_text(
                urlparse(url).path
            )
        except Exception:
            return ""

    def _get_url(self, page):
        return self._normalize_text(
            getattr(page, "url", "")
        )

    def _add_signal(
        self,
        signals,
        page_type,
        source,
        value,
        weight,
    ):
        signals.append(
            {
                "page_type": page_type,
                "source": source,
                "value": value,
                "weight": weight,
            }
        )

    def _structured_data_signals(self, jsonld_types):
        signals = []

        for jsonld_type in jsonld_types:
            if jsonld_type == "product":
                self._add_signal(
                    signals,
                    "product",
                    "json_ld",
                    "Product",
                    10,
                )

            elif jsonld_type in {
                "article",
                "newsarticle",
                "blogposting",
            }:
                self._add_signal(
                    signals,
                    "article",
                    "json_ld",
                    jsonld_type,
                    10,
                )

            elif jsonld_type in {
                "collectionpage",
                "itemlist",
                "category",
            }:
                self._add_signal(
                    signals,
                    "category",
                    "json_ld",
                    jsonld_type,
                    8,
                )

            elif jsonld_type in {
                "faqpage",
            }:
                self._add_signal(
                    signals,
                    "faq",
                    "json_ld",
                    jsonld_type,
                    10,
                )

            elif jsonld_type in {
                "contactpage",
            }:
                self._add_signal(
                    signals,
                    "contact",
                    "json_ld",
                    jsonld_type,
                    10,
                )

            elif jsonld_type in {
                "aboutpage",
            }:
                self._add_signal(
                    signals,
                    "about",
                    "json_ld",
                    jsonld_type,
                    10,
                )

        return signals

    def _path_signals(self, path):
        signals = []

        path_parts = [
            part
            for part in path.strip("/").split("/")
            if part
        ]

        path_text = " ".join(path_parts)

        if not path_parts:
            self._add_signal(
                signals,
                "homepage",
                "url_path",
                "/",
                10,
            )

            return signals

        patterns = {
            "product": [
                r"(^|/)(product|products|item|items)(/|$)",
            ],
            "category": [
                r"(^|/)(category|categories|collection|collections)(/|$)",
            ],
            "article": [
                r"(^|/)(blog|article|articles|news|posts|stories)(/|$)",
            ],
            "documentation": [
                r"(^|/)(docs|documentation|help|guides|guide|manual)(/|$)",
            ],
            "pricing": [
                r"(^|/)(pricing|plans|price)(/|$)",
            ],
            "contact": [
                r"(^|/)(contact|contact-us|get-in-touch)(/|$)",
            ],
            "about": [
                r"(^|/)(about|about-us|company)(/|$)",
            ],
            "faq": [
                r"(^|/)(faq|faqs|frequently-asked-questions)(/|$)",
            ],
            "search": [
                r"(^|/)(search)(/|$)",
            ],
            "login": [
                r"(^|/)(login|signin|sign-in|account)(/|$)",
            ],
        }

        for page_type, regexes in patterns.items():
            for pattern in regexes:
                if re.search(pattern, path):
                    self._add_signal(
                        signals,
                        page_type,
                        "url_path",
                        path,
                        6,
                    )
                    break

        return signals

    def _text_signals(
        self,
        title,
        h1,
        h2,
    ):
        signals = []

        combined = " ".join(
            value
            for value in [
                title,
                h1,
                h2,
            ]
            if value
        )

        text_patterns = {
            "pricing": [
                "pricing",
                "plans",
                "price",
            ],
            "contact": [
                "contact us",
                "contact",
                "get in touch",
            ],
            "about": [
                "about us",
                "about",
                "our company",
            ],
            "faq": [
                "faq",
                "frequently asked questions",
            ],
            "documentation": [
                "documentation",
                "getting started",
                "developer guide",
                "user guide",
                "api reference",
            ],
            "article": [
                "blog",
                "article",
                "news",
                "posted",
                "published",
            ],
            "product": [
                "product",
                "buy now",
                "add to cart",
                "shop",
            ],
            "login": [
                "log in",
                "login",
                "sign in",
                "signin",
            ],
            "search": [
                "search results",
                "search",
            ],
        }

        for page_type, keywords in text_patterns.items():
            for keyword in keywords:
                if keyword in combined:
                    self._add_signal(
                        signals,
                        page_type,
                        "page_text",
                        keyword,
                        3,
                    )
                    break

        return signals

    def classify(self, page):
        """
        Classify a single PageResult.
        """

        jsonld_types = self._get_jsonld_types(page)
        path = self._get_path(page)
        url = self._get_url(page)
        title = self._get_title(page)
        h1 = self._get_h1(page)
        h2 = self._get_h2(page)

        signals = []

        signals.extend(
            self._structured_data_signals(
                jsonld_types
            )
        )

        signals.extend(
            self._path_signals(path)
        )

        signals.extend(
            self._text_signals(
                title,
                h1,
                h2,
            )
        )

        # ---------------------------------------------------------
        # Score page types
        # ---------------------------------------------------------

        scores = {}

        for signal in signals:
            page_type = signal["page_type"]

            scores[page_type] = (
                scores.get(page_type, 0)
                + signal["weight"]
            )

        if scores:
            ranked = sorted(
                scores.items(),
                key=lambda item: (
                    item[1],
                    item[0],
                ),
                reverse=True,
            )

            primary_type = ranked[0][0]
            primary_score = ranked[0][1]

        else:
            primary_type = "other"
            primary_score = 0

        # ---------------------------------------------------------
        # Confidence
        # ---------------------------------------------------------

        if primary_type == "other":
            confidence = "low"

        elif primary_score >= 10:
            confidence = "high"

        elif primary_score >= 6:
            confidence = "medium"

        else:
            confidence = "low"

        # ---------------------------------------------------------
        # Supporting types
        # ---------------------------------------------------------

        supporting_types = [
            page_type
            for page_type, score in sorted(
                scores.items(),
                key=lambda item: (
                    item[1],
                    item[0],
                ),
                reverse=True,
            )
            if page_type != primary_type
            and score >= 3
        ]

        return {
            "url": url,
            "primary_type": primary_type,
            "confidence": confidence,
            "score": primary_score,
            "supporting_types": supporting_types,
            "evidence": {
                "json_ld_types": jsonld_types,
                "url_path": path,
                "title": title,
                "h1": getattr(
                    page,
                    "h1",
                    [],
                ) or [],
                "h2": getattr(
                    page,
                    "h2",
                    [],
                ) or [],
                "signals": signals,
                "scores": scores,
            },
        }

    def classify_site(self, pages):
        """
        Classify all crawled pages and return site-level evidence.
        """

        results = []

        type_counts = {}

        for page in pages:
            result = self.classify(page)

            results.append(result)

            page_type = result["primary_type"]

            type_counts[page_type] = (
                type_counts.get(page_type, 0)
                + 1
            )

        return {
            "pages_classified": len(pages),
            "type_counts": type_counts,
            "pages": results,
        }