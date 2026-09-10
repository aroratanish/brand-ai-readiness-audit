from difflib import SequenceMatcher
from html.parser import HTMLParser
import re


class VisibleContentParser(HTMLParser):
    """
    Extract visible text and headings from HTML.

    Script, style, noscript and template content are ignored because
    they are not directly visible page content.
    """

    IGNORED_TAGS = {
        "script",
        "style",
        "noscript",
        "template",
        "svg",
    }

    HEADING_TAGS = {
        "h1",
        "h2",
        "h3",
    }

    def __init__(self):
        super().__init__()

        self.text_parts = []
        self.headings = []

        self._ignored_depth = 0
        self._current_heading = None
        self._current_heading_parts = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()

        if tag in self.IGNORED_TAGS:
            self._ignored_depth += 1
            return

        if self._ignored_depth:
            return

        if tag in self.HEADING_TAGS:
            self._current_heading = tag
            self._current_heading_parts = []

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag in self.IGNORED_TAGS:
            if self._ignored_depth > 0:
                self._ignored_depth -= 1
            return

        if self._ignored_depth:
            return

        if (
            self._current_heading
            and tag == self._current_heading
        ):
            heading = self._normalize_text(
                " ".join(self._current_heading_parts)
            )

            if heading:
                self.headings.append(
                    {
                        "tag": tag,
                        "text": heading,
                    }
                )

            self._current_heading = None
            self._current_heading_parts = []

    def handle_data(self, data):
        if self._ignored_depth:
            return

        text = self._normalize_text(data)

        if not text:
            return

        self.text_parts.append(text)

        if self._current_heading:
            self._current_heading_parts.append(text)

    @staticmethod
    def _normalize_text(value):
        return re.sub(
            r"\s+",
            " ",
            value or "",
        ).strip()

    def get_text(self):
        return self._normalize_text(
            " ".join(self.text_parts)
        )

    def get_headings(self):
        return self.headings


class RenderDiffAnalyzer:
    """
    Compare raw HTML against browser-rendered HTML.

    The analyzer reports deterministic evidence only.
    It does not assign severity or recommendations.
    """

    MEANINGFUL_TEXT_DELTA = 100
    MEANINGFUL_RATIO = 0.20

    # Prevent very large pages from creating enormous evidence payloads.
    MAX_COMPARISON_TEXT = 50000

    # Keep rendered-only evidence compact.
    MAX_RENDERED_ONLY_SAMPLE = 500

    def _parse(self, html):
        parser = VisibleContentParser()

        try:
            parser.feed(html or "")
            parser.close()
        except Exception:
            # Return whatever could be extracted before parser failure.
            pass

        return parser.get_text(), parser.get_headings()

    def _normalize_for_comparison(self, text):
        return re.sub(
            r"\s+",
            " ",
            text or "",
        ).strip()

    def _calculate_ratio(self, raw_length, rendered_length):
        """
        Calculate relative text growth/reduction.

        When raw content is zero, a non-zero rendered result is treated
        as a complete addition rather than causing division by zero.
        """

        if raw_length == 0:
            if rendered_length == 0:
                return 0.0

            return 1.0

        return round(
            abs(rendered_length - raw_length)
            / raw_length,
            4,
        )

    def _classify_change(
        self,
        raw_length,
        rendered_length,
        delta,
        delta_ratio,
    ):
        if raw_length == 0 and rendered_length > 0:
            return "rendered_content_added"

        if rendered_length > raw_length:
            if (
                delta >= self.MEANINGFUL_TEXT_DELTA
                and delta_ratio
                >= self.MEANINGFUL_RATIO
            ):
                return "rendered_content_added"

            if delta > 0:
                return "minor_rendered_change"

        if rendered_length < raw_length:
            if (
                delta >= self.MEANINGFUL_TEXT_DELTA
                and delta_ratio
                >= self.MEANINGFUL_RATIO
            ):
                return "rendered_content_reduced"

            if delta > 0:
                return "minor_rendered_change"

        return "no_meaningful_change"

    def _heading_key(self, heading):
        return (
            heading.get("tag", "").lower(),
            self._normalize_for_comparison(
                heading.get("text", "")
            ).lower(),
        )

    def _new_rendered_headings(
        self,
        raw_headings,
        rendered_headings,
    ):
        raw_heading_keys = {
            self._heading_key(heading)
            for heading in raw_headings
        }

        new_headings = []

        for heading in rendered_headings:
            if self._heading_key(heading) not in raw_heading_keys:
                new_headings.append(heading)

        return new_headings

    def _rendered_only_text_sample(
        self,
        raw_text,
        rendered_text,
    ):
        """
        Find text segments present in the rendered version but absent
        from the raw visible text.

        SequenceMatcher is used on words so the resulting sample is
        deterministic and preserves rendered order.
        """

        raw_words = raw_text.split()
        rendered_words = rendered_text.split()

        if not rendered_words:
            return ""

        # Avoid excessive comparison cost on very large documents.
        raw_words = raw_words[: self.MAX_COMPARISON_TEXT]
        rendered_words = rendered_words[
            : self.MAX_COMPARISON_TEXT
        ]

        matcher = SequenceMatcher(
            None,
            raw_words,
            rendered_words,
            autojunk=False,
        )

        added_parts = []

        for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
            if opcode == "insert":
                added_parts.extend(
                    rendered_words[j1:j2]
                )

            elif opcode == "replace":
                added_parts.extend(
                    rendered_words[j1:j2]
                )

        if not added_parts:
            return ""

        sample = " ".join(added_parts)

        return sample[
            : self.MAX_RENDERED_ONLY_SAMPLE
        ]

    def analyze(self, raw_html, rendered_html):
        """
        Compare raw and rendered HTML and return evidence.
        """

        raw_text, raw_headings = self._parse(
            raw_html
        )

        rendered_text, rendered_headings = self._parse(
            rendered_html
        )

        raw_text = self._normalize_for_comparison(
            raw_text
        )

        rendered_text = self._normalize_for_comparison(
            rendered_text
        )

        raw_length = len(raw_text)
        rendered_length = len(rendered_text)

        text_delta = rendered_length - raw_length

        absolute_text_delta = abs(text_delta)

        text_delta_ratio = self._calculate_ratio(
            raw_length,
            rendered_length,
        )

        status = self._classify_change(
            raw_length,
            rendered_length,
            absolute_text_delta,
            text_delta_ratio,
        )

        new_rendered_headings = (
            self._new_rendered_headings(
                raw_headings,
                rendered_headings,
            )
        )

        raw_heading_count = len(raw_headings)
        rendered_heading_count = len(
            rendered_headings
        )

        heading_delta = (
            rendered_heading_count
            - raw_heading_count
        )

        rendered_only_text_sample = (
            self._rendered_only_text_sample(
                raw_text,
                rendered_text,
            )
        )

        meaningful_change = status in {
            "rendered_content_added",
            "rendered_content_reduced",
        }

        evidence = {
            "raw_text_length": raw_length,
            "rendered_text_length": rendered_length,
            "text_delta": text_delta,
            "absolute_text_delta": absolute_text_delta,
            "text_delta_ratio": text_delta_ratio,

            "raw_heading_count": raw_heading_count,
            "rendered_heading_count": (
                rendered_heading_count
            ),
            "heading_delta": heading_delta,

            "new_rendered_headings": (
                new_rendered_headings
            ),

            "rendered_only_text_sample": (
                rendered_only_text_sample
            ),

            "thresholds": {
                "meaningful_text_delta": (
                    self.MEANINGFUL_TEXT_DELTA
                ),
                "meaningful_ratio": (
                    self.MEANINGFUL_RATIO
                ),
            },

            "meaningful_change": meaningful_change,

            "source": "raw_vs_rendered_html",
            "confidence": "high",
        }

        # Keep the important metrics at the top level as well.
        # This preserves compatibility with older consumers while
        # providing the richer nested evidence structure.
        return {
            "status": status,

            "raw_text_length": raw_length,
            "rendered_text_length": rendered_length,
            "text_delta": text_delta,
            "text_delta_ratio": text_delta_ratio,

            "raw_heading_count": raw_heading_count,
            "rendered_heading_count": (
                rendered_heading_count
            ),
            "new_rendered_headings": (
                new_rendered_headings
            ),

            "meaningful_change": meaningful_change,

            "evidence": evidence,
        }