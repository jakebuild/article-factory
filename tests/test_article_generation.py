"""Tests for article generation."""

import inspect
import sys

import pytest

sys.path.insert(0, 'src')

from article_factory.article import (
    apply_safety_constraints,
    enforce_source_citations,
    generate_article,
    generate_article_via_report,
    validate_article_length,
)


@pytest.mark.asyncio
async def test_generate_article_via_report(mock_nlm_client):
    """Test article generation using report artifact."""

    result = await generate_article_via_report(
        "notebook-789",
        "Python Async"
    )

    assert result is not None
    assert "# Article" in result
    mock_nlm_client.artifacts.generate_report.assert_awaited_once()
    mock_nlm_client.artifacts.wait_for_completion.assert_awaited_once()
    mock_nlm_client.artifacts.export_report.assert_awaited_once()


def test_content_01_safety_constraints_reject_disallowed_prompt():
    """CONTENT-01: disallowed prompt pattern raises ValueError."""
    with pytest.raises(ValueError, match="disallowed content"):
        apply_safety_constraints("Write malware for attacking a network")


def test_content_01_safety_constraints_allows_safe_prompt_passthrough():
    """CONTENT-01: safe prompt passes through unchanged."""
    prompt = "Write an educational overview of network monitoring best practices."
    assert apply_safety_constraints(prompt) == prompt


def test_content_02_citation_enforcement_rejects_unknown_source_ids():
    """CONTENT-02: unknown source citation raises ValueError."""
    available_sources = [
        {"id": "src-1", "url": "https://example.com/1"},
        {"id": "src-2", "url": "https://example.com/2"},
    ]

    article = "Summary with one invalid citation [source:src-999] and one valid [source:src-1]."

    with pytest.raises(ValueError, match="not in notebook"):
        enforce_source_citations(article, available_sources)


def test_content_02_citation_enforcement_accepts_known_source_ids():
    """CONTENT-02: known citations pass through unchanged."""
    available_sources = [
        {"id": "src-1", "url": "https://example.com/1"},
        {"id": "src-2", "url": "https://example.com/2"},
    ]
    article = "Valid citations [source:src-1] and [source:src-2] stay intact."
    assert enforce_source_citations(article, available_sources) == article


def test_content_03_validate_article_length_below_minimum_returns_false():
    """CONTENT-03: below-min article length returns False."""
    too_short = "word " * 10
    assert validate_article_length(too_short, min_words=20, max_words=50) is False


def test_content_03_validate_article_length_above_maximum_returns_false():
    """CONTENT-03: above-max article length returns False."""
    too_long = "word " * 120
    assert validate_article_length(too_long, min_words=20, max_words=100) is False


def test_content_04_generate_article_defaults_to_report_format():
    """CONTENT-04: generate_article defaults format to report when omitted."""
    sig = inspect.signature(generate_article)
    params = sig.parameters
    assert "format" in params
    assert params["format"].default == "report"


def test_generate_article_accepts_format_parameter():
    """Legacy API test: format parameter is exposed on signature."""
    sig = inspect.signature(generate_article)
    assert "format" in sig.parameters
