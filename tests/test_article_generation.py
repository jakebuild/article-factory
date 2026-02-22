"""Tests for article generation."""

import pytest
import sys

sys.path.insert(0, 'src')

from article_factory.article import generate_article_via_report


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


def test_generate_article_format_option():
    """Test that generate_article accepts format parameter."""
    import inspect
    from article_factory.article import generate_article
    sig = inspect.signature(generate_article)
    params = sig.parameters
    assert "format" in params
