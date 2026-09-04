from skills.crawl_render_audit.scripts.metadata_analyzer import MetadataAnalyzer
from skills.crawl_render_audit.scripts.canonical_analyzer import CanonicalAnalyzer
from skills.crawl_render_audit.scripts.jsonld_analyzer import JSONLDAnalyzer
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