from __future__ import annotations

from typing import Any

from skills.crawl_render_audit.scripts.models import PageResult
from skills.crawl_render_audit.scripts.page_type_classifier import PageTypeClassifier

from .scripts.engagement_adapter import adapt_page_result
from .scripts.engagement_checks import run_checks


SOURCE_SKILL = "engagement-audit"


def _page_context(page: PageResult) -> dict[str, Any]:
    evidence = adapt_page_result(page)
    page_type = evidence.get("page_type")
    if not isinstance(page_type, dict):
        page_type = PageTypeClassifier().classify(page)
        evidence["page_type"] = page_type

    if isinstance(page_type, dict):
        primary = page_type.get("primary_type")
        confidence = page_type.get("confidence")
        supporting = set(page_type.get("supporting_types") or [])
        url_path = str(getattr(page, "url", "") or "").lower()
        product_like_path = any(token in url_path for token in ("/product", "/products", "/shop", "/store"))

        if (
            primary in {"product", "pricing", "contact"}
            and confidence in {"high", "medium"}
        ) or (
            "product" in supporting and confidence in {"high", "medium", "low"}
        ) or (
            product_like_path and confidence in {"high", "medium", "low"}
        ):
            evidence["high_intent"] = True

    return evidence


def findings_for_page(page: PageResult) -> list[dict[str, Any]]:
    """Run the deterministic engagement pipeline for one crawled PageResult."""
    return run_checks(_page_context(page))


def engagement_stub(url: str) -> list[dict[str, Any]]:
    """Compatibility shim for callers that explicitly disable engagement."""
    return []


__all__ = ["findings_for_page", "engagement_stub"]
