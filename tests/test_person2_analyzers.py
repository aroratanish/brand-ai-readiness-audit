from skills.crawl_render_audit.scripts.metadata_analyzer import MetadataAnalyzer
from skills.crawl_render_audit.scripts.canonical_analyzer import CanonicalAnalyzer
from skills.crawl_render_audit.scripts.jsonld_analyzer import JSONLDAnalyzer
from skills.crawl_render_audit.scripts.page_type_classifier import (
    PageTypeClassifier,
)
from skills.crawl_render_audit.scripts.render_diff_analyzer import (
    RenderDiffAnalyzer,
)
from skills.crawl_render_audit.scripts.llm_discoverability_analyzer import (
    LLMDiscoverabilityAnalyzer,
)


def test_metadata_missing_title():
    analyzer = MetadataAnalyzer()

    result = analyzer.analyze(
        None,
        "This is a sufficiently long description for testing purposes.",
        ["Main heading"],
        [],
    )

    title_check = next(
        item for item in result
        if item["check"] == "title"
    )

    assert title_check["status"] == "missing"


def test_metadata_valid_values():
    analyzer = MetadataAnalyzer()

    result = analyzer.analyze(
        "Example Website",
        "This is a sufficiently long description that provides useful information about the page.",
        ["Main heading"],
        ["Section heading"],
    )

    statuses = {
        item["check"]: item["status"]
        for item in result
    }

    assert statuses["title"] == "ok"
    assert statuses["meta_description"] == "ok"
    assert statuses["h1"] == "ok"


def test_canonical_missing():
    analyzer = CanonicalAnalyzer()

    result = analyzer.analyze(
        "https://example.com/page",
        None,
    )

    assert result["status"] == "missing"


def test_canonical_self_referencing():
    analyzer = CanonicalAnalyzer()

    result = analyzer.analyze(
        "https://example.com/page",
        "https://example.com/page",
    )

    assert result["status"] == "self_referencing"


def test_jsonld_missing():
    analyzer = JSONLDAnalyzer()

    result = analyzer.analyze([])

    assert result["status"] == "missing"


def test_jsonld_valid():
    analyzer = JSONLDAnalyzer()

    result = analyzer.analyze(
        [
            {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": "Test Article",
            }
        ]
    )

    assert result["status"] == "present"
    assert "Article" in result["evidence"]["types"]

    assert result["status"] == "present"


def test_llm_structured_data_missing():
    analyzer = LLMDiscoverabilityAnalyzer()

    result = analyzer._check_structured_data([])

    assert result["present"] is False
    assert result["valid_blocks"] == 0


def test_llm_structured_data_present():
    analyzer = LLMDiscoverabilityAnalyzer()

    result = analyzer._check_structured_data(
        [
            {
                "@context": "https://schema.org",
                "@type": "Article",
            }
        ]
    )

    assert result["present"] is True
    assert result["valid_blocks"] == 1
    assert "Article" in result["types"]


def test_llm_rendered_content_change():
    analyzer = LLMDiscoverabilityAnalyzer()

    result = analyzer._check_rendered_content(
        {"status": "success"},
        {
            "status": "rendered_content_added",
            "meaningful_change": True,
        },
    )

    assert result["render_status"] == "success"
    assert result["meaningful_change"] is True


def test_llm_rendered_content_failure():
    analyzer = LLMDiscoverabilityAnalyzer()

    result = analyzer._check_rendered_content(
        {
            "status": "error",
            "error": "test error",
        },
        {
            "status": "no_meaningful_change",
            "meaningful_change": False,
        },
    )

    assert result["render_status"] == "error"
    assert result["meaningful_change"] is False

from types import SimpleNamespace

from skills.crawl_render_audit.scripts.cross_signal_analyzer import (
    CrossSignalAnalyzer,
)


def test_cross_signal_rendered_content_dependency():
    page = SimpleNamespace(
        url="https://example.com/product",
        raw_html="<html></html>",
        rendered_html=(
            "<html><body>"
            "<h1>Product</h1>"
            "<p>Important product content</p>"
            "</body></html>"
        ),
        redirect_chain=[],
        technical_evidence={
            "render": {
                "status": "success",
            },
            "raw_vs_rendered": {
                "status": "rendered_content_added",
                "evidence": {
                    "raw_text_length": 20,
                    "rendered_text_length": 200,
                    "text_delta": 180,
                    "text_delta_ratio": 9.0,
                },
            },
            "json_ld": {
                "status": "present",
                "evidence": {
                    "types": ["Product"],
                },
            },
            "metadata": [
                {
                    "check": "title",
                    "status": "ok",
                },
                {
                    "check": "h1",
                    "status": "ok",
                },
            ],
        },
    )

    analyzer = CrossSignalAnalyzer()

    result = analyzer.analyze_page(page)

    signal_names = [
        signal["signal"]
        for signal in result["signals"]
    ]

    assert (
        "rendered_content_dependency"
        in signal_names
    )


def test_cross_signal_structured_data_render_relationship():
    page = SimpleNamespace(
        url="https://example.com/product",
        raw_html="<html></html>",
        rendered_html="<html>content</html>",
        redirect_chain=[],
        technical_evidence={
            "render": {
                "status": "success",
            },
            "raw_vs_rendered": {
                "status": "rendered_content_added",
                "evidence": {
                    "raw_text_length": 10,
                    "rendered_text_length": 100,
                    "text_delta": 90,
                    "text_delta_ratio": 9.0,
                },
            },
            "json_ld": {
                "status": "present",
                "evidence": {
                    "types": ["Product"],
                },
            },
            "metadata": [],
        },
    )

    analyzer = CrossSignalAnalyzer()

    result = analyzer.analyze_page(page)

    relationship = [
        signal
        for signal in result["signals"]
        if signal["signal"]
        == "structured_data_render_relationship"
    ]

    assert len(relationship) == 1

    assert (
        relationship[0]["evidence"][
            "structured_data"
        ]
        == "structured_data_present"
    )


def test_cross_signal_core_metadata_gap():
    page = SimpleNamespace(
        url="https://example.com/page",
        raw_html="<html></html>",
        rendered_html="<html></html>",
        redirect_chain=[],
        technical_evidence={
            "metadata": [
                {
                    "check": "title",
                    "status": "missing",
                },
                {
                    "check": "h1",
                    "status": "missing",
                },
            ],
        },
    )

    analyzer = CrossSignalAnalyzer()

    result = analyzer.analyze_page(page)

    signal_names = [
        signal["signal"]
        for signal in result["signals"]
    ]

    assert "core_metadata_gap" in signal_names


def test_cross_signal_site_summary():
    page = SimpleNamespace(
        url="https://example.com",
        raw_html="<html></html>",
        rendered_html="<html></html>",
        redirect_chain=[],
        technical_evidence={
            "metadata": [],
        },
    )

    analyzer = CrossSignalAnalyzer()

    result = analyzer.analyze_site([page])

    assert result["pages_analyzed"] == 1
    assert "signal_counts" in result
    assert "pages" in result


def test_page_type_product_from_json_ld():
    page = SimpleNamespace(
        url="https://example.com/item/phone",
        title="Smart Phone",
        h1=["Smart Phone"],
        h2=["Specifications"],
        json_ld=[],
        technical_evidence={
            "json_ld": {
                "status": "present",
                "evidence": {
                    "types": ["Product"],
                },
            }
        },
    )

    classifier = PageTypeClassifier()

    result = classifier.classify(page)

    assert result["primary_type"] == "product"
    assert result["confidence"] == "high"


def test_page_type_documentation_from_url():
    page = SimpleNamespace(
        url="https://example.com/docs/getting-started",
        title="Getting Started",
        h1=["Getting Started"],
        h2=["Installation"],
        json_ld=[],
        technical_evidence={},
    )

    classifier = PageTypeClassifier()

    result = classifier.classify(page)

    assert result["primary_type"] == "documentation"
    assert result["confidence"] == "medium"


def test_page_type_homepage():
    page = SimpleNamespace(
        url="https://example.com/",
        title="Example",
        h1=["Welcome"],
        h2=[],
        json_ld=[],
        technical_evidence={},
    )

    classifier = PageTypeClassifier()

    result = classifier.classify(page)

    assert result["primary_type"] == "homepage"
    assert result["confidence"] == "high"


def test_page_type_site_summary():
    page = SimpleNamespace(
        url="https://example.com/pricing",
        title="Pricing",
        h1=["Plans and Pricing"],
        h2=[],
        json_ld=[],
        technical_evidence={},
    )

    classifier = PageTypeClassifier()

    result = classifier.classify_site([page])

    assert result["pages_classified"] == 1
    assert result["type_counts"]["pricing"] == 1
    assert len(result["pages"]) == 1



def test_render_diff_detects_meaningful_rendered_content():
    analyzer = RenderDiffAnalyzer()

    raw_html = """
    <html>
        <body>
            <h1>Product</h1>
        </body>
    </html>
    """

    rendered_html = """
    <html>
        <body>
            <h1>Product</h1>
            <h2>Features</h2>
            <p>
                This is important product information
                that appears after JavaScript rendering.
                It contains enough text to exceed the
                meaningful change threshold.
            </p>
        </body>
    </html>
    """

    result = analyzer.analyze(
        raw_html,
        rendered_html,
    )

    assert result["status"] == "rendered_content_added"

    assert (
        result["evidence"]["rendered_text_length"]
        > result["evidence"]["raw_text_length"]
    )

    assert (
        result["evidence"]["absolute_text_delta"]
        >= 100
    )

    assert (
        result["evidence"]["meaningful_change"]
        is True
    )


def test_render_diff_detects_new_rendered_heading():
    analyzer = RenderDiffAnalyzer()

    raw_html = """
    <html>
        <body>
            <h1>Product</h1>
        </body>
    </html>
    """

    rendered_html = """
    <html>
        <body>
            <h1>Product</h1>
            <h2>Specifications</h2>
            <h3>Technical Details</h3>
        </body>
    </html>
    """

    result = analyzer.analyze(
        raw_html,
        rendered_html,
    )

    headings = result["evidence"][
        "new_rendered_headings"
    ]

    heading_texts = [
        heading["text"].lower()
        for heading in headings
    ]

    assert "specifications" in heading_texts
    assert "technical details" in heading_texts


def test_render_diff_returns_rendered_only_text_sample():
    analyzer = RenderDiffAnalyzer()

    raw_html = """
    <html>
        <body>
            <h1>Product</h1>
        </body>
    </html>
    """

    rendered_html = """
    <html>
        <body>
            <h1>Product</h1>
            <p>
                This content exists only after rendering.
                JavaScript populated this section.
            </p>
        </body>
    </html>
    """

    result = analyzer.analyze(
        raw_html,
        rendered_html,
    )

    sample = result["evidence"][
        "rendered_only_text_sample"
    ]

    assert isinstance(sample, str)
    assert len(sample) <= 500


def test_render_diff_no_meaningful_change():
    analyzer = RenderDiffAnalyzer()

    html = """
    <html>
        <body>
            <h1>Example</h1>
            <p>Hello world</p>
        </body>
    </html>
    """

    result = analyzer.analyze(
        html,
        html,
    )

    assert (
        result["status"]
        == "no_meaningful_change"
    )

    assert (
        result["evidence"]["text_delta"]
        == 0
    )

    assert (
        result["evidence"]["meaningful_change"]
        is False
    )