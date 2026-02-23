"""Tests for NotebookLM infographic wrapper behavior."""

import asyncio
from unittest.mock import ANY, AsyncMock, MagicMock, call

import pytest
from notebooklm._artifacts import ArtifactStatus

from article_factory.notebook_lm import NotebookLMClientWrapper


INFOGRAPHIC = 7


class _ClientContext:
    def __init__(self, client):
        self._client = client

    async def __aenter__(self):
        return self._client

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _artifact(artifact_id, status):
    return [artifact_id, None, INFOGRAPHIC, None, status]


@pytest.mark.asyncio
async def test_nlm_01_generate_infographic_deletes_failed_artifacts_before_trigger(monkeypatch):
    raw_before = [
        _artifact("failed-1", ArtifactStatus.FAILED),
        _artifact("completed-existing", ArtifactStatus.COMPLETED),
        _artifact("failed-2", ArtifactStatus.FAILED),
    ]
    raw_after_trigger = [
        _artifact("completed-existing", ArtifactStatus.COMPLETED),
        _artifact("new-artifact", 0),
    ]
    raw_after_poll = [_artifact("new-artifact", ArtifactStatus.COMPLETED)]

    client = MagicMock()
    client.artifacts = MagicMock()
    client.artifacts._list_raw = AsyncMock(
        side_effect=[raw_before, raw_after_trigger, raw_after_poll]
    )
    client.artifacts.delete = AsyncMock()
    client.artifacts.generate_infographic = AsyncMock(return_value=None)

    wrapper = NotebookLMClientWrapper()
    monkeypatch.setattr(wrapper, "get_client", AsyncMock(return_value=_ClientContext(client)))
    monkeypatch.setattr(asyncio, "sleep", AsyncMock(return_value=None))

    result = await wrapper.generate_infographic("nb-nlm-01", instructions="build chart")

    assert result == {"task_id": "new-artifact"}
    assert client.artifacts.delete.await_args_list == [
        call("nb-nlm-01", "failed-1"),
        call("nb-nlm-01", "failed-2"),
    ]
    client.artifacts.generate_infographic.assert_awaited_once()
    assert client.artifacts._list_raw.await_count == 3


@pytest.mark.asyncio
async def test_nlm_02_generate_infographic_tracks_new_artifact_from_diff(monkeypatch):
    raw_before = [_artifact("completed-existing", ArtifactStatus.COMPLETED)]
    raw_after_trigger = [
        _artifact("completed-existing", ArtifactStatus.COMPLETED),
        _artifact("new-generated", ArtifactStatus.COMPLETED),
    ]
    raw_after_poll = [
        _artifact("completed-existing", ArtifactStatus.COMPLETED),
        _artifact("new-generated", ArtifactStatus.COMPLETED),
    ]

    client = MagicMock()
    client.artifacts = MagicMock()
    client.artifacts._list_raw = AsyncMock(
        side_effect=[raw_before, raw_after_trigger, raw_after_poll]
    )
    client.artifacts.delete = AsyncMock()
    client.artifacts.generate_infographic = AsyncMock(return_value=None)

    wrapper = NotebookLMClientWrapper()
    monkeypatch.setattr(wrapper, "get_client", AsyncMock(return_value=_ClientContext(client)))
    monkeypatch.setattr(asyncio, "sleep", AsyncMock(return_value=None))

    result = await wrapper.generate_infographic("nb-nlm-02")

    assert result == {"task_id": "new-generated"}
    assert result["task_id"] != "completed-existing"
    client.artifacts.delete.assert_not_awaited()
    client.artifacts.generate_infographic.assert_awaited_once_with(
        "nb-nlm-02",
        instructions=None,
        orientation=ANY,
        detail_level=ANY,
    )
    assert client.artifacts._list_raw.await_count == 3


@pytest.mark.asyncio
async def test_nlm_03_generate_infographic_polls_until_completed_and_returns_task_id(monkeypatch):
    raw_before = [_artifact("completed-existing", ArtifactStatus.COMPLETED)]
    raw_after_trigger = [
        _artifact("completed-existing", ArtifactStatus.COMPLETED),
        _artifact("new-polling", 0),
    ]
    raw_poll_pending = [_artifact("new-polling", 0)]
    raw_poll_completed = [_artifact("new-polling", ArtifactStatus.COMPLETED)]

    client = MagicMock()
    client.artifacts = MagicMock()
    client.artifacts._list_raw = AsyncMock(
        side_effect=[raw_before, raw_after_trigger, raw_poll_pending, raw_poll_completed]
    )
    client.artifacts.delete = AsyncMock()
    client.artifacts.generate_infographic = AsyncMock(return_value=None)

    wrapper = NotebookLMClientWrapper()
    monkeypatch.setattr(wrapper, "get_client", AsyncMock(return_value=_ClientContext(client)))
    monkeypatch.setattr(asyncio, "sleep", AsyncMock(return_value=None))

    result = await wrapper.generate_infographic("nb-nlm-03")

    assert result == {"task_id": "new-polling"}
    client.artifacts.generate_infographic.assert_awaited_once()
    assert client.artifacts._list_raw.await_count == 4


@pytest.mark.asyncio
async def test_nlm_04_generate_infographic_raises_when_poll_status_failed(monkeypatch):
    raw_before = [_artifact("completed-existing", ArtifactStatus.COMPLETED)]
    raw_after_trigger = [
        _artifact("completed-existing", ArtifactStatus.COMPLETED),
        _artifact("new-failed", 0),
    ]
    raw_poll_failed = [_artifact("new-failed", ArtifactStatus.FAILED)]

    client = MagicMock()
    client.artifacts = MagicMock()
    client.artifacts._list_raw = AsyncMock(
        side_effect=[raw_before, raw_after_trigger, raw_poll_failed]
    )
    client.artifacts.delete = AsyncMock()
    client.artifacts.generate_infographic = AsyncMock(return_value=None)

    wrapper = NotebookLMClientWrapper()
    monkeypatch.setattr(wrapper, "get_client", AsyncMock(return_value=_ClientContext(client)))
    monkeypatch.setattr(asyncio, "sleep", AsyncMock(return_value=None))

    with pytest.raises(RuntimeError, match="FAILED status"):
        await wrapper.generate_infographic("nb-nlm-04")

    client.artifacts.generate_infographic.assert_awaited_once()
    assert client.artifacts._list_raw.await_count == 3
