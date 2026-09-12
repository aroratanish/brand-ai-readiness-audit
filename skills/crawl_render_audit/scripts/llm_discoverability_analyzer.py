import json
from urllib.parse import urljoin, urlparse

import requests


class LLMDiscoverabilityAnalyzer:
    def __init__(self, timeout=10):
        self.timeout = timeout

    def _check_llms_txt(self, page_url):
        parsed = urlparse(page_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        llms_url = urljoin(base_url + "/", "llms.txt")

        result = {
            "url": llms_url,
            "status_code": None,
            "exists": False,
            "content_type": None,
            "content_length": 0,
            "valid_text": False,
            "error": None,
        }

        try:
            response = requests.get(
                llms_url,
                timeout=self.timeout,
                allow_redirects=True,
                headers={
                    "User-Agent": "BrandAIReadinessAudit/1.0"
                },
            )

            result["status_code"] = response.status_code
            result["exists"] = response.status_code == 200
            result["content_type"] = response.headers.get("content-type")
            result["content_length"] = len(response.content)

            content_type = (result["content_type"] or "").lower()

            result["valid_text"] = (
                response.status_code == 200
                and (
                    "text/plain" in content_type
                    or "text/" in content_type
                    or content_type == ""
                )
                and bool(response.text.strip())
            )

        except requests.RequestException as exc:
            result["error"] = str(exc)

        return result

    def _check_structured_data(self, json_ld):
        if not json_ld:
            return {
                "present": False,
                "valid_blocks": 0,
                "types": [],
            }

        valid_blocks = 0
        types = set()

        for block in json_ld:
            if not isinstance(block, dict):
                continue

            valid_blocks += 1

            value = block.get("@type")

            if isinstance(value, str):
                types.add(value)

            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        types.add(item)

        return {
            "present": valid_blocks > 0,
            "valid_blocks": valid_blocks,
            "types": sorted(types),
        }

    def _check_rendered_content(self, render_evidence, render_diff):
        render_status = None
        render_error = None
        meaningful_change = False
        change_status = None

        if isinstance(render_evidence, dict):
            render_status = render_evidence.get("status")
            render_error = render_evidence.get("error")

        if isinstance(render_diff, dict):
            meaningful_change = bool(
                render_diff.get("meaningful_change", False)
            )
            change_status = render_diff.get("status")

        return {
            "render_status": render_status,
            "render_error": render_error,
            "meaningful_change": meaningful_change,
            "change_status": change_status,
        }

    def analyze_page(
        self,
        page_url,
        json_ld=None,
        render_evidence=None,
        render_diff=None,
    ):
        llms_txt = self._check_llms_txt(page_url)

        structured_data = self._check_structured_data(json_ld)

        rendered_content = self._check_rendered_content(
            render_evidence,
            render_diff,
        )

        return {
            "llms_txt": llms_txt,
            "structured_data": structured_data,
            "rendered_content": rendered_content,
        }

    def analyze_site(self, site_url, pages):
        llms_txt = self._check_llms_txt(site_url)

        pages_with_structured_data = 0
        pages_without_structured_data = 0

        pages_with_rendered_changes = 0
        render_failures = 0

        structured_data_types = set()

        for page in pages:
            evidence = getattr(page, "technical_evidence", {}) or {}

            json_ld = evidence.get("json_ld", {})
            if isinstance(json_ld, dict):
                if json_ld.get("status") == "present":
                    pages_with_structured_data += 1
                elif json_ld.get("status") == "missing":
                    pages_without_structured_data += 1

                for value in json_ld.get("types", []):
                    structured_data_types.add(value)

            render = evidence.get("render", {})
            if isinstance(render, dict):
                if render.get("status") == "error":
                    render_failures += 1

            render_diff = evidence.get("raw_vs_rendered", {})
            if isinstance(render_diff, dict):
                if render_diff.get("meaningful_change"):
                    pages_with_rendered_changes += 1

        return {
            "llms_txt": llms_txt,
            "structured_data": {
                "pages_with_json_ld": pages_with_structured_data,
                "pages_without_json_ld": pages_without_structured_data,
                "types": sorted(structured_data_types),
            },
            "rendering": {
                "pages_with_meaningful_render_changes": pages_with_rendered_changes,
                "render_failures": render_failures,
            },
        }