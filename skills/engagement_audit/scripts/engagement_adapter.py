from __future__ import annotations

from dataclasses import asdict, is_dataclass
from html.parser import HTMLParser
from typing import Any, Mapping
from urllib.parse import urljoin

from ..crawl_render_audit.scripts.models import PageResult


class _EngagementHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)

        self.links: list[dict[str, Any]] = []
        self.buttons: list[dict[str, Any]] = []
        self.forms: list[dict[str, Any]] = []

        self._current_link: dict[str, Any] | None = None
        self._current_button: dict[str, Any] | None = None
        self._current_form: dict[str, Any] | None = None

        self._text_stack: list[str] = []

    @staticmethod
    def _attrs(
        attrs: list[tuple[str, str | None]],
    ) -> dict[str, str]:
        return {
            key: value or ""
            for key, value in attrs
        }

    def _text(self) -> str:
        return " ".join(
            part.strip()
            for part in self._text_stack
            if part.strip()
        )

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attrs_map = self._attrs(attrs)

        if tag == "a":
            self._current_link = {
                "href": attrs_map.get("href", ""),
                "text": "",
                "aria_label": attrs_map.get("aria-label", ""),
                "title": attrs_map.get("title", ""),
                "role": attrs_map.get("role", ""),
            }
            self._text_stack = []

        elif tag == "button":
            button = {
                "type": attrs_map.get("type", ""),
                "text": "",
                "aria_label": attrs_map.get("aria-label", ""),
                "title": attrs_map.get("title", ""),
                "role": attrs_map.get("role", ""),
            }

            if self._current_form is not None:
                control = {
                    "tag": "button",
                    "type": attrs_map.get("type", ""),
                    "name": attrs_map.get("name", ""),
                    "value": attrs_map.get("value", ""),
                    "aria_label": attrs_map.get("aria-label", ""),
                    "title": attrs_map.get("title", ""),
                    "required": "required" in attrs_map,
                }

                self._current_form["controls"].append(control)

                if attrs_map.get("type", "").lower() in {"", "submit"}:
                    self._current_form["has_submit"] = True

            self._current_button = button
            self._text_stack = []

        elif tag == "form":
            self._current_form = {
                "action": attrs_map.get("action", ""),
                "method": attrs_map.get("method", ""),
                "controls": [],
                "has_submit": False,
                "aria_label": attrs_map.get("aria-label", ""),
                "name": attrs_map.get("name", ""),
            }

        elif tag in {"input", "select", "textarea"}:
            if self._current_form is not None:
                control_type = attrs_map.get("type", "")

                control = {
                    "tag": tag,
                    "type": control_type,
                    "name": attrs_map.get("name", ""),
                    "value": attrs_map.get("value", ""),
                    "aria_label": attrs_map.get("aria-label", ""),
                    "placeholder": attrs_map.get("placeholder", ""),
                    "title": attrs_map.get("title", ""),
                    "required": "required" in attrs_map,
                }

                self._current_form["controls"].append(control)

                if (
                    tag == "input"
                    and control_type.lower() in {"submit", "image"}
                ):
                    self._current_form["has_submit"] = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current_link is not None:
            self._current_link["text"] = self._text()
            self.links.append(self._current_link)
            self._current_link = None
            self._text_stack = []

        elif tag == "button" and self._current_button is not None:
            self._current_button["text"] = self._text()
            self.buttons.append(self._current_button)
            self._current_button = None
            self._text_stack = []

        elif tag == "form" and self._current_form is not None:
            self.forms.append(self._current_form)
            self._current_form = None

    def handle_data(self, data: str) -> None:
        if self._current_link is not None:
            self._text_stack.append(data)

        if self._current_button is not None:
            self._text_stack.append(data)


def _page_dict(
    page: PageResult | Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(page, Mapping):
        return dict(page)

    if is_dataclass(page):
        return asdict(page)

    raise TypeError("Expected PageResult or mapping")


def _parse_html(html: str) -> _EngagementHTMLParser:
    parser = _EngagementHTMLParser()

    if not html:
        return parser

    try:
        parser.feed(html)
        parser.close()
    except Exception:
        return parser

    return parser


def _normalise_url(
    page_url: str,
    target: str,
) -> str:
    target = str(target or "").strip()

    if not target:
        return ""

    return urljoin(page_url, target)


def _link_evidence(
    parser: _EngagementHTMLParser,
    page_url: str,
) -> list[dict[str, Any]]:
    evidence = []

    for link in parser.links:
        href = str(link.get("href") or "").strip()

        evidence.append(
            {
                "href": href,
                "absolute_url": _normalise_url(
                    page_url,
                    href,
                ),
                "text": str(
                    link.get("text") or ""
                ).strip(),
                "aria_label": str(
                    link.get("aria_label") or ""
                ).strip(),
                "title": str(
                    link.get("title") or ""
                ).strip(),
                "role": str(
                    link.get("role") or ""
                ).strip(),
            }
        )

    return evidence


def _button_evidence(
    parser: _EngagementHTMLParser,
) -> list[dict[str, Any]]:
    evidence = []

    for button in parser.buttons:
        evidence.append(
            {
                "type": str(
                    button.get("type") or ""
                ).strip(),
                "text": str(
                    button.get("text") or ""
                ).strip(),
                "aria_label": str(
                    button.get("aria_label") or ""
                ).strip(),
                "title": str(
                    button.get("title") or ""
                ).strip(),
                "role": str(
                    button.get("role") or ""
                ).strip(),
            }
        )

    return evidence


def _form_evidence(
    parser: _EngagementHTMLParser,
    page_url: str,
) -> list[dict[str, Any]]:
    evidence = []

    for form in parser.forms:
        action = str(
            form.get("action") or ""
        ).strip()

        controls = list(
            form.get("controls") or []
        )

        evidence.append(
            {
                "action": action,
                "absolute_action": (
                    _normalise_url(
                        page_url,
                        action,
                    )
                    if action
                    else page_url
                ),
                "method": str(
                    form.get("method") or ""
                ).strip(),
                "aria_label": str(
                    form.get("aria_label") or ""
                ).strip(),
                "name": str(
                    form.get("name") or ""
                ).strip(),
                "controls": controls,
                "has_submit": (
                    form.get("has_submit") is True
                ),
            }
        )

    return evidence


def build_engagement_evidence(
    page: PageResult | Mapping[str, Any],
) -> dict[str, Any]:
    data = _page_dict(page)

    rendered_html = str(
        data.get("rendered_html") or ""
    )

    raw_html = str(
        data.get("raw_html") or ""
    )

    html = rendered_html or raw_html

    parser = _parse_html(html)

    page_url = str(
        data.get("final_url")
        or data.get("url")
        or ""
    ).strip()

    return {
        "url": str(
            data.get("url") or ""
        ).strip(),
        "final_url": str(
            data.get("final_url") or ""
        ).strip(),
        "status_code": data.get("status_code"),
        "redirect_chain": list(
            data.get("redirect_chain") or []
        ),
        "title": data.get("title"),
        "meta_description": data.get(
            "meta_description"
        ),
        "h1": list(
            data.get("h1") or []
        ),
        "h2": list(
            data.get("h2") or []
        ),
        "canonical": data.get("canonical"),
        "internal_links": list(
            data.get("internal_links") or []
        ),
        "external_links": list(
            data.get("external_links") or []
        ),
        "json_ld": list(
            data.get("json_ld") or []
        ),
        "errors": list(
            data.get("errors") or []
        ),
        "links": _link_evidence(
            parser,
            page_url,
        ),
        "buttons": _button_evidence(
            parser,
        ),
        "forms": _form_evidence(
            parser,
            page_url,
        ),
    }


def adapt_page_result(
    page: PageResult | Mapping[str, Any],
) -> dict[str, Any]:
    return build_engagement_evidence(page)
