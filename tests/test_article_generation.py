"""Tests for article generation."""

import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
sys.path.insert(0, 'src')

from article_factory.article import generate_article_via_report


@pytest.mark.asyncio
async def test_generate_article_via_report():
    """Test article generation using report artifact."""

    mock_client = MagicMock()

    mock_status = MagicMock()
    mock_status.id = "artifact-123"
    mock_client.artifacts.generate_report = AsyncMock(return_value=mock_status)

    mock_result = MagicMock()
    mock_result.artifact_id = "artifact-456"
    mock_client.artifacts.wait_for_completion = AsyncMock(return_value=mock_result)

    mock_client.artifacts.export_report = AsyncMock(return_value="# Article\n\nContent...")

    result = await generate_article_via_report(
        mock_client,
        "notebook-789",
        "Python Async"
    )

    assert result is not None
    assert "# Article" in result
    mock_client.artifacts.generate_report.assert_called_once()
    mock_client.artifacts.export_report.assert_called_once()


def test_generate_article_format_option():
    """Test that generate_article accepts format parameter."""
    import inspect
    from article_factory.article import generate_article
    sig = inspect.signature(generate_article)
    params = sig.parameters
    assert "format" in params
