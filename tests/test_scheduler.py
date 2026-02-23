"""Scheduler tests for async task orchestration and retries."""

import subprocess
import sys
from unittest.mock import AsyncMock

import pytest

from article_factory.database import create_topic, get_topic, increment_retry, update_status
from article_factory.models import TopicStatus
from article_factory.scheduler import _execute_pipeline, create_task, get_task, run_pipeline_async


def test_pipe_01_run_pipeline_async_creates_task_and_spawns_detached_worker(monkeypatch):
    created_topic = create_topic(
        topic="PIPE-01 scheduler topic",
        prompt="Validate task creation and detached process spawn",
    )
    assert created_topic is not None

    popen_calls = []

    def fake_popen(*args, **kwargs):
        popen_calls.append((args, kwargs))

        class _DummyProcess:
            pass

        return _DummyProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    task_id = run_pipeline_async(created_topic["id"], prompt="inline prompt")

    assert isinstance(task_id, str)
    assert len(task_id) == 36
    assert task_id.count("-") == 4

    persisted_task = get_task(task_id)
    assert persisted_task is not None
    assert persisted_task["id"] == task_id
    assert persisted_task["topic_id"] == created_topic["id"]
    assert persisted_task["status"] == "PENDING"

    assert len(popen_calls) == 1
    args, kwargs = popen_calls[0]
    assert args == (
        [sys.executable, "-m", "article_factory.main", "worker", task_id],
    )
    assert kwargs["start_new_session"] is True
    assert kwargs["stdout"] is subprocess.DEVNULL
    assert kwargs["stderr"] is subprocess.DEVNULL


@pytest.mark.asyncio
async def test_pipe_02_execute_pipeline_advances_stages_in_documented_order(monkeypatch):
    created_topic = create_topic(
        topic="PIPE-02 scheduler topic",
        prompt="Validate stage ordering",
    )
    assert created_topic is not None

    import article_factory.article as article_module
    import article_factory.audio as audio_module
    import article_factory.media as media_module
    import article_factory.notebooks as notebooks_module
    import article_factory.output as output_module
    import article_factory.scheduler as scheduler_module
    import article_factory.research as research_module

    monkeypatch.setattr(
        notebooks_module,
        "create_notebook_for_topic",
        AsyncMock(return_value="notebook-1"),
    )
    monkeypatch.setattr(
        notebooks_module,
        "trigger_deep_research",
        AsyncMock(return_value="research-task-1"),
    )
    monkeypatch.setattr(
        notebooks_module,
        "wait_for_research_completion",
        AsyncMock(return_value={"sources_imported": 3}),
    )
    monkeypatch.setattr(
        research_module,
        "generate_synthesis",
        AsyncMock(return_value="# Synthesis"),
    )
    monkeypatch.setattr(
        article_module,
        "generate_article",
        AsyncMock(return_value="# Article"),
    )
    monkeypatch.setattr(
        media_module,
        "generate_infographic",
        AsyncMock(return_value="/tmp/infographic.png"),
    )
    monkeypatch.setattr(
        audio_module,
        "generate_audio_briefing",
        AsyncMock(return_value="/tmp/audio.mp3"),
    )
    monkeypatch.setattr(
        output_module,
        "export_all_artifacts",
        lambda *_args, **_kwargs: {
            "output_dir": "2026-02-23__pipe-02",
            "article": "article.md",
            "infographic": "infographic.png",
        },
    )

    recorded_stages = []

    def record_notify(_task_id, stage, _progress_percent, _message=None):
        recorded_stages.append(stage)

    monkeypatch.setattr(scheduler_module, "notify_progress", record_notify)

    task_id = create_task(created_topic["id"], prompt="Generate article")
    await _execute_pipeline(task_id)

    assert recorded_stages == [
        "NOTEBOOK_CREATED",
        "RESEARCH_TRIGGERED",
        "RESEARCH_COMPLETED",
        "SYNTHESIS_DONE",
        "ARTICLE_DONE",
        "MEDIA_DONE",
        "COMPLETED",
    ]


@pytest.mark.asyncio
async def test_pipe_03_execute_pipeline_records_failed_stage_error_message(monkeypatch):
    created_topic = create_topic(
        topic="PIPE-03 scheduler topic",
        prompt="Validate failed stage recording",
    )
    assert created_topic is not None

    import article_factory.media as media_module
    import article_factory.notebooks as notebooks_module
    import article_factory.research as research_module

    monkeypatch.setattr(
        notebooks_module,
        "create_notebook_for_topic",
        AsyncMock(return_value="notebook-2"),
    )
    monkeypatch.setattr(
        notebooks_module,
        "trigger_deep_research",
        AsyncMock(return_value="research-task-2"),
    )
    monkeypatch.setattr(
        notebooks_module,
        "wait_for_research_completion",
        AsyncMock(return_value={"sources_imported": 1}),
    )
    monkeypatch.setattr(
        research_module,
        "generate_synthesis",
        AsyncMock(return_value="# Synthesis"),
    )

    async def raise_infographic_error(_topic_id):
        raise RuntimeError("pipeline infographic failure")

    monkeypatch.setattr(media_module, "generate_infographic", raise_infographic_error)

    task_id = create_task(created_topic["id"], prompt="Generate article")
    await _execute_pipeline(task_id)

    persisted_task = get_task(task_id)
    assert persisted_task is not None
    assert persisted_task["status"] == "FAILED"
    assert persisted_task["error_message"] is not None
    assert "Infographic generation failed: pipeline infographic failure" in persisted_task["error_message"]


@pytest.mark.asyncio
async def test_pipe_04_retry_requeues_topic_below_max_retries(monkeypatch):
    created_topic = create_topic(
        topic="PIPE-04 retry below max",
        prompt="Validate retry re-queue path",
    )
    assert created_topic is not None
    topic_id = created_topic["id"]

    assert update_status(topic_id, TopicStatus.PENDING) is not None
    assert update_status(topic_id, TopicStatus.PROCESSING) is not None

    import article_factory.notebooks as notebooks_module

    monkeypatch.setattr(
        notebooks_module,
        "create_notebook_for_topic",
        AsyncMock(side_effect=RuntimeError("retryable notebook failure")),
    )

    task_id = create_task(topic_id)
    await _execute_pipeline(task_id)

    persisted_task = get_task(task_id)
    assert persisted_task is not None
    assert persisted_task["status"] == "FAILED"

    persisted_topic = get_topic(topic_id)
    assert persisted_topic is not None
    assert persisted_topic["retry_count"] == 1
    assert persisted_topic["status"] == TopicStatus.PENDING.value


@pytest.mark.asyncio
async def test_pipe_04_retry_stops_requeue_at_max_retries(monkeypatch):
    created_topic = create_topic(
        topic="PIPE-04 retry max reached",
        prompt="Validate retry cap path",
    )
    assert created_topic is not None
    topic_id = created_topic["id"]

    assert update_status(topic_id, TopicStatus.PENDING) is not None
    assert update_status(topic_id, TopicStatus.PROCESSING) is not None
    assert increment_retry(topic_id) is not None
    assert increment_retry(topic_id) is not None

    import article_factory.notebooks as notebooks_module

    monkeypatch.setattr(
        notebooks_module,
        "create_notebook_for_topic",
        AsyncMock(side_effect=RuntimeError("terminal notebook failure")),
    )

    task_id = create_task(topic_id)
    await _execute_pipeline(task_id)

    persisted_topic = get_topic(topic_id)
    assert persisted_topic is not None
    assert persisted_topic["retry_count"] == 3
    assert persisted_topic["status"] == TopicStatus.FAILED.value
