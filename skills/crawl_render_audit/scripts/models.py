from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LinkResult:
    url: str

    status_code: Optional[int] = None
    success: bool = False

    final_url: Optional[str] = None

    redirected: bool = False
    redirect_chain: list[str] = field(
        default_factory=list
    )

    content_type: str = ""

    classification: str = ""

    error: Optional[str] = None


@dataclass
class PageResult:
    url: str
    depth: int

    status_code: Optional[int] = None
    final_url: Optional[str] = None

    redirect_chain: list[str] = field(
        default_factory=list
    )

    raw_html: str = ""
    rendered_html: str = ""

    title: Optional[str] = None
    meta_description: Optional[str] = None

    h1: list[str] = field(
        default_factory=list
    )

    h2: list[str] = field(
        default_factory=list
    )

    canonical: Optional[str] = None

    internal_links: list[str] = field(
        default_factory=list
    )

    external_links: list[str] = field(
        default_factory=list
    )

    json_ld: list[dict] = field(
        default_factory=list
    )

    link_results: list[LinkResult] = field(
        default_factory=list
    )

    technical_evidence: dict = field(
        default_factory=dict
    )

    errors: list[str] = field(
        default_factory=list
    )