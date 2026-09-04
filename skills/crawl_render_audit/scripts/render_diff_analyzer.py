from html import unescape
from html.parser import HTMLParser
import re


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.ignore_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript", "template"}:
            self.ignore_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript", "template"}:
            if self.ignore_depth > 0:
                self.ignore_depth -= 1

    def handle_data(self, data):
        if self.ignore_depth == 0:
            text = data.strip()
            if text:
                self.parts.append(text)

    def get_text(self):
        return " ".join(self.parts)


class RenderDiffAnalyzer:
    def __init__(
        self,
        meaningful_text_delta: int = 100,
        meaningful_ratio: float = 0.20,
    ):
        self.meaningful_text_delta = meaningful_text_delta
        self.meaningful_ratio = meaningful_ratio

    def _extract_text(self, html):
        if not html:
            return ""

        try:
            parser = TextExtractor()
            parser.feed(html)
            text = unescape(parser.get_text())
        except Exception:
            text = re.sub(r"<[^>]+>", " ", html)

        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _normalize_text(self, text):
        return re.sub(r"\s+", " ", text).strip()

    def _extract_headings(self, html):
        if not html:
            return []

        headings = re.findall(
            r"<h[1-6][^>]*>(.*?)</h[1-6]>",
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )

        cleaned = []

        for heading in headings:
            heading = re.sub(r"<[^>]+>", " ", heading)
            heading = unescape(heading)
            heading = re.sub(r"\s+", " ", heading).strip()

            if heading:
                cleaned.append(heading)

        return cleaned

    def analyze(self, raw_html, rendered_html):
        raw_text = self._extract_text(raw_html)
        rendered_text = self._extract_text(rendered_html)

        raw_text = self._normalize_text(raw_text)
        rendered_text = self._normalize_text(rendered_text)

        raw_length = len(raw_text)
        rendered_length = len(rendered_text)

        delta = rendered_length - raw_length

        if raw_length > 0:
            ratio = delta / raw_length
        elif rendered_length > 0:
            ratio = 1.0
        else:
            ratio = 0.0

        raw_headings = self._extract_headings(raw_html)
        rendered_headings = self._extract_headings(rendered_html)

        new_headings = [
            heading
            for heading in rendered_headings
            if heading not in raw_headings
        ]

        meaningful_change = (
            delta >= self.meaningful_text_delta
            and ratio >= self.meaningful_ratio
        )

        if meaningful_change:
            status = "rendered_content_added"
        elif rendered_length > raw_length:
            status = "minor_rendered_change"
        elif rendered_length < raw_length:
            status = "rendered_content_reduced"
        else:
            status = "no_meaningful_change"

        return {
            "check": "raw_vs_rendered_html",
            "status": status,
            "evidence": {
                "raw_text_length": raw_length,
                "rendered_text_length": rendered_length,
                "text_length_delta": delta,
                "text_length_ratio": round(ratio, 3),
                "raw_heading_count": len(raw_headings),
                "rendered_heading_count": len(rendered_headings),
                "new_rendered_headings": new_headings[:20],
                "meaningful_change": meaningful_change,
            },
        }