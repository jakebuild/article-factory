"""Tests for research orchestration and synthesis behavior."""

from unittest.mock import AsyncMock

import pytest

from article_factory import research


class _FakeLoopClock:
    def __init__(self, times):
        self._times = list(times)

    def time(self):
        if len(self._times) == 1:
            return self._times[0]
        return self._times.pop(0)


class _SourceObject:
    def __init__(self, source_id, title, url=""):
        self.id = source_id
        self.title = title
        self.url = url


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


@pytest.mark.asyncio
async def test_res_02_poll_research_raises_timeout_when_elapsed_exceeds_limit(monkeypatch):
    topic_id = 202
    notebook_id = "notebook-res-02"

    update_status_calls = []
    increment_retry_calls = []

    def fake_get_topic(requested_topic_id):
        assert requested_topic_id == topic_id
        return {
            "id": topic_id,
            "topic": "RES 02 Topic",
            "status": "PROCESSING",
            "notebook_id": notebook_id,
        }

    def fake_update_status(requested_topic_id, new_status):
        update_status_calls.append((requested_topic_id, str(new_status)))

    def fake_increment_retry(requested_topic_id):
        increment_retry_calls.append(requested_topic_id)

    wrapper = AsyncMock()
    wrapper.poll_research = AsyncMock(return_value={"status": "in_progress"})

    fake_loop = _FakeLoopClock([100.0, 100.1, 101.2])

    monkeypatch.setattr(research, "get_topic", fake_get_topic)
    monkeypatch.setattr(research, "update_status", fake_update_status)
    monkeypatch.setattr(research, "increment_retry", fake_increment_retry)
    monkeypatch.setattr(research, "NotebookLMClientWrapper", lambda: wrapper)
    monkeypatch.setattr(research.asyncio, "get_event_loop", lambda: fake_loop)
    monkeypatch.setattr(research.asyncio, "sleep", AsyncMock(return_value=None))

    with pytest.raises(TimeoutError):
        await research.poll_research(topic_id, poll_interval=1, timeout=1)

    wrapper.poll_research.assert_awaited_once_with(notebook_id)
    assert update_status_calls == []
    assert increment_retry_calls == []


@pytest.mark.asyncio
async def test_res_03_generate_synthesis_returns_string_content(monkeypatch):
    notebook_id = "notebook-res-03"

    wrapper = AsyncMock()
    wrapper.list_sources = AsyncMock(
        return_value=[
            _SourceObject("src-obj-1", "Imported Object Source"),
            {"id": "src-dict-2", "title": "Imported Dict Source"},
        ]
    )
    wrapper.poll_research = AsyncMock(
        return_value={
            "status": "completed",
            "sources": [
                _SourceObject("disc-obj", "Discovered Object Source", "https://example.com/object"),
                {"title": "Discovered Dict Source", "url": "https://example.com/dict"},
            ],
            "summary": "Key findings from offline synthesis test.",
        }
    )

    monkeypatch.setattr(research, "NotebookLMClientWrapper", lambda: wrapper)

    synthesis = await research.generate_synthesis(notebook_id, "res-03-topic")

    assert isinstance(synthesis, str)
    assert synthesis


@pytest.mark.asyncio
async def test_res_04_generate_synthesis_includes_sources_and_summary_sections(monkeypatch):
    notebook_id = "notebook-res-04"

    wrapper = AsyncMock()
    wrapper.list_sources = AsyncMock(
        return_value=[_SourceObject("src-100", "Imported Source 100")]
    )
    wrapper.poll_research = AsyncMock(
        return_value={
            "status": "completed",
            "sources": [
                {"title": "Discovered Source A", "url": "https://example.com/a"}
            ],
            "summary": "This is the research summary body.",
        }
    )

    monkeypatch.setattr(research, "NotebookLMClientWrapper", lambda: wrapper)

    synthesis = await research.generate_synthesis(notebook_id, "res-04-topic")

    assert "## Discovered Sources" in synthesis
    assert "Discovered Source A" in synthesis
    assert "## Research Summary" in synthesis
    assert "This is the research summary body." in synthesis
