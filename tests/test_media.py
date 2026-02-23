"""Tests for media output path resolution and infographic idempotency."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import article_factory.media as media_module


class TopicRecord:
    """ORM-like topic shape exposing attributes used by media helpers."""

    def __init__(self, topic, created_at, notebook_id=None):
        self.topic = topic
        self.created_at = created_at
        self.notebook_id = notebook_id


def test_content_05_get_output_dir_supports_dict_topic_shape(monkeypatch):
    """CONTENT-05: get_output_dir resolves expected path from dict topic."""
    topic = {
        "topic": "AI Safety",
        "created_at": "2026-02-20T10:30:00",
    }

    mkdir_calls = []
    monkeypatch.setattr(media_module, "get_topic", lambda _: topic)
    monkeypatch.setattr(
        media_module.os,
        "makedirs",
        lambda path, exist_ok=False: mkdir_calls.append((path, exist_ok)),
    )

    output_dir = media_module.get_output_dir(1)

    assert output_dir == "output/2026-02-20__ai-safety"
    assert mkdir_calls == [("output/2026-02-20__ai-safety", True)]


def test_content_05_get_output_dir_supports_object_topic_shape(monkeypatch):
    """CONTENT-05: get_output_dir resolves expected path from ORM-like object topic."""
    topic = TopicRecord("Quantum Computing", datetime(2026, 1, 15, 9, 0, 0))

    mkdir_calls = []
    monkeypatch.setattr(media_module, "get_topic", lambda _: topic)
    monkeypatch.setattr(
        media_module.os,
        "makedirs",
        lambda path, exist_ok=False: mkdir_calls.append((path, exist_ok)),
    )

    output_dir = media_module.get_output_dir(1)

    assert output_dir == "output/2026-01-15__quantum-computing"
    assert mkdir_calls == [("output/2026-01-15__quantum-computing", True)]


@pytest.mark.asyncio
async def test_content_06_generate_infographic_returns_existing_file_without_wrapper_calls(
    monkeypatch, tmp_path
):
    """CONTENT-06: existing infographic short-circuits wrapper generation/download."""
    topic = {"notebook_id": "nb-123", "topic": "AI Safety", "created_at": "2026-02-20T10:30:00"}
    existing_path = tmp_path / "infographic.png"

    wrapper = SimpleNamespace(
        generate_infographic=AsyncMock(return_value={"task_id": "unused"}),
        download_infographic=AsyncMock(return_value=str(existing_path)),
    )

    monkeypatch.setattr(media_module, "get_topic", lambda _: topic)
    monkeypatch.setattr(media_module, "get_output_dir", lambda _: str(tmp_path))
    monkeypatch.setattr(media_module.os.path, "exists", lambda path: path == str(existing_path))
    monkeypatch.setattr(media_module, "NotebookLMClientWrapper", lambda: wrapper)

    image_path = await media_module.generate_infographic(1)

    assert image_path == str(existing_path)
    wrapper.generate_infographic.assert_not_awaited()
    wrapper.download_infographic.assert_not_awaited()
