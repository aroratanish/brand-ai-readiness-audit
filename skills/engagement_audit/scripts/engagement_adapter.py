from __future__ import annotations

from dataclasses import asdict, is_dataclass
from html.parser import HTMLParser
from typing import Any, Mapping
from urllib.parse import urljoin

from skills.crawl_render_audit.scripts.models import PageResult


class _EngagementHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, Any]] = []
        self.buttons: list[dict[str, Any]] = []
        self.forms: list[dict[str, Any]] = []
        self.title: str = ""
        self.meta_description: str = ""
        self.h1: list[str] = []
        self.h2: list[str] = []
        self._heading_tag: str | None = None
        self._heading_text: list[str] = []
        self._current_link: dict[str, Any] | None = None
        self._current_button: dict[str, Any] | None = None
        self._current_form: dict[str, Any] | None = None
        self._text_stack: list[str] = []

    @staticmethod
    def _attrs(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {key.lower(): value or "" for key, value in attrs}

    def _text(self) -> str:
        return " ".join(part.strip() for part in self._text_stack if part.strip())

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = self._attrs(attrs)

        if tag == "title":
            self._heading_tag = "title"
            self._heading_text = []
            return

        if tag == "meta" and attrs_map.get("name", "").lower() == "description":
            self.meta_description = attrs_map.get("content", "").strip()
            return

        if tag in {"h1", "h2"}:
            self._heading_tag = tag
            self._heading_text = []
            return

        if tag == "a":
            self._current_link = {
                "href": attrs_map.get("href", ""),
                "text": "",
                "aria_label": attrs_map.get("aria-label", ""),
                "title": attrs_map.get("title", ""),
                "role": attrs_map.get("role", ""),
            }
            self._text_stack = []
            return

        if tag == "button":
            self._current_button = {
                "type": attrs_map.get("type", ""),
                "text": "",
                "aria_label": attrs_map.get("aria-label", ""),
                "title": attrs_map.get("title", ""),
                "role": attrs_map.get("role", ""),
            }
            if self._current_form is not None:
                control_type = attrs_map.get("type", "").lower()
                self._current_form["controls"].append(
                    {
                        "tag": "button",
                        "type": attrs_map.get("type", ""),
                        "name": attrs_map.get("name", ""),
                        "value": attrs_map.get("value", ""),
                        "aria_label": attrs_map.get("aria-label", ""),
                        "title": attrs_map.get("title", ""),
                        "required": "required" in attrs_map,
                    }
                )
                if control_type in {"", "submit"}:
                    self._current_form["has_submit"] = True
            self._text_stack = []
            return

        if tag == "form":
            self._current_form = {
                "action": attrs_map.get("action", ""),
                "method": attrs_map.get("method", ""),
                "controls": [],
                "has_submit": False,
                "aria_label": attrs_map.get("aria-label", ""),
                "name": attrs_map.get("name", ""),
            }
            return

        if tag in {"input", "select", "textarea"} and self._current_form is not None:
            control_type = attrs_map.get("type", "")
            self._current_form["controls"].append(
                {
                    "tag": tag,
                    "type": control_type,
                    "name": attrs_map.get("name", ""),
                    "value": attrs_map.get("value", ""),
                    "aria_label": attrs_map.get("aria-label", ""),
                    "placeholder": attrs_map.get("placeholder", ""),
                    "title": attrs_map.get("title", ""),
                    "required": "required" in attrs_map,
                }
            )
            if tag == "input" and control_type.lower() in {"submit", "image"}:
                self._current_form["has_submit"] = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._heading_tag == "title":
            self.title = " ".join(self._heading_text).strip()
            self._heading_tag = None
            self._heading_text = []
            return

        if tag in {"h1", "h2"} and self._heading_tag == tag:
            value = " ".join(self._heading_text).strip()
            if value:
                (self.h1 if tag == "h1" else self.h2).append(value)
            self._heading_tag = None
            self._heading_text = []
            return

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
        if self._heading_tag is not None:
            self._heading_text.append(data)
        if self._current_link is not None or self._current_button is not None:
            self._text_stack.append(data)


def _page_dict(page: PageResult | Mapping[str, Any]) -> dict[str, Any]:
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


def _absolute(page_url: str, target: Any) -> str:
    value = str(target or "").strip()
    return urljoin(page_url, value) if value else ""


def _link_status_index(data: Mapping[str, Any], page_url: str) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for result in data.get("link_results") or []:
        if not isinstance(result, Mapping):
            continue
        raw_url = str(result.get("url") or "").strip()
        absolute = _absolute(page_url, raw_url)
        if absolute:
            index[absolute] = dict(result)
    return index


def build_engagement_evidence(page: PageResult | Mapping[str, Any]) -> dict[str, Any]:
    data = _page_dict(page)
    rendered_html = str(data.get("rendered_html") or "")
    raw_html = str(data.get("raw_html") or "")
    parser = _parse_html(rendered_html or raw_html)
    page_url = str(data.get("final_url") or data.get("url") or "").strip()
    status_index = _link_status_index(data, page_url)

    links: list[dict[str, Any]] = []
    for link in parser.links:
        href = str(link.get("href") or "").strip()
        absolute_url = _absolute(page_url, href)
        observed = status_index.get(absolute_url, {})
        links.append(
            {
                "href": href,
                "absolute_url": absolute_url,
                "text": str(link.get("text") or "").strip(),
                "aria_label": str(link.get("aria_label") or "").strip(),
                "title": str(link.get("title") or "").strip(),
                "role": str(link.get("role") or "").strip(),
                "status_code": observed.get("status_code"),
                "success": observed.get("success"),
                "final_url": observed.get("final_url"),
                "redirected": observed.get("redirected"),
                "classification": observed.get("classification"),
                "error": observed.get("error"),
            }
        )

    buttons = [
        {
            "type": str(button.get("type") or "").strip(),
            "text": str(button.get("text") or "").strip(),
            "aria_label": str(button.get("aria_label") or "").strip(),
            "title": str(button.get("title") or "").strip(),
            "role": str(button.get("role") or "").strip(),
        }
        for button in parser.buttons
    ]

    forms = []
    for form in parser.forms:
        action = str(form.get("action") or "").strip()
        forms.append(
            {
                "action": action,
                "absolute_action": _absolute(page_url, action) if action else page_url,
                "method": str(form.get("method") or "").strip(),
                "aria_label": str(form.get("aria_label") or "").strip(),
                "name": str(form.get("name") or "").strip(),
                "controls": list(form.get("controls") or []),
                "has_submit": form.get("has_submit") is True,
            }
        )

    technical_evidence = data.get("technical_evidence")
    page_type = technical_evidence.get("page_type") if isinstance(technical_evidence, Mapping) else None

    return {
        "url": str(data.get("url") or "").strip(),
        "final_url": str(data.get("final_url") or "").strip(),
        "status_code": data.get("status_code"),
        "redirect_chain": list(data.get("redirect_chain") or []),
        "title": data.get("title") or parser.title,
        "meta_description": data.get("meta_description") or parser.meta_description,
        "h1": list(data.get("h1") or parser.h1),
        "h2": list(data.get("h2") or parser.h2),
        "canonical": data.get("canonical"),
        "internal_links": list(data.get("internal_links") or []),
        "external_links": list(data.get("external_links") or []),
        "json_ld": list(data.get("json_ld") or []),
        "errors": list(data.get("errors") or []),
        "links": links,
        "buttons": buttons,
        "forms": forms,
        "page_type": page_type,
    }


def adapt_page_result(page: PageResult | Mapping[str, Any]) -> dict[str, Any]:
    return build_engagement_evidence(page)
