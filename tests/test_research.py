"""Tests for research orchestration and synthesis behavior."""

from unittest.mock import AsyncMock

import pytest

from article_factory import research


@pytest.mark.asyncio
async def test_res_01_run_research_starts_polls_and_imports_sources(monkeypatch):
    topic_id = 101
    notebook_id = "notebook-res-01"
    task_id = "task-res-01"
    discovered_sources = [
        {"title": "Async Orchestration", "url": "https://example.com/async"},
        {"title": "Research Polling", "url": "https://example.com/polling"},
    ]
    imported_sources = [{"id": "src-1"}, {"id": "src-2"}]

    update_status_calls = []
    set_notebook_id_calls = []
    increment_retry_calls = []

    def fake_get_topic(requested_topic_id):
        assert requested_topic_id == topic_id
        return {
            "id": topic_id,
            "topic": "RES 01 Topic",
            "prompt": "Investigate offline research flow",
            "status": "PENDING",
            "notebook_id": notebook_id,
        }

    def fake_set_notebook_id(requested_topic_id, requested_notebook_id):
        set_notebook_id_calls.append((requested_topic_id, requested_notebook_id))

    def fake_update_status(requested_topic_id, new_status):
        update_status_calls.append((requested_topic_id, str(new_status)))

    def fake_increment_retry(requested_topic_id):
        increment_retry_calls.append(requested_topic_id)

    wrapper = AsyncMock()
    wrapper.create_notebook = AsyncMock(return_value=notebook_id)
    wrapper.start_research = AsyncMock(return_value={"task_id": task_id})
    wrapper.poll_research = AsyncMock(
        side_effect=[
            {"status": "in_progress"},
            {"status": "completed", "sources": discovered_sources},
        ]
    )
    wrapper.import_sources = AsyncMock(return_value=imported_sources)

    monkeypatch.setattr(research, "get_topic", fake_get_topic)
    monkeypatch.setattr(research, "set_notebook_id", fake_set_notebook_id)
    monkeypatch.setattr(research, "update_status", fake_update_status)
    monkeypatch.setattr(research, "increment_retry", fake_increment_retry)
    monkeypatch.setattr(research, "NotebookLMClientWrapper", lambda: wrapper)
    monkeypatch.setattr(research.asyncio, "sleep", AsyncMock(return_value=None))

    result = await research.run_research(topic_id)

    wrapper.create_notebook.assert_awaited_once_with("RES 01 Topic")
    wrapper.start_research.assert_awaited_once_with(
        notebook_id,
        "Investigate offline research flow",
    )
    assert wrapper.poll_research.await_count == 2
    wrapper.import_sources.assert_awaited_once_with(notebook_id, task_id, discovered_sources)

    assert result["status"] == "completed"
    assert result["sources"] == discovered_sources
    assert result["notebook_id"] == notebook_id
    assert result["imported_sources"] == imported_sources
    assert set_notebook_id_calls == [(topic_id, notebook_id)]
    assert update_status_calls[0] == (topic_id, "PROCESSING")
    assert update_status_calls[-1] == (topic_id, "COMPLETED")
    assert increment_retry_calls == []
