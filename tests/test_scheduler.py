"""Scheduler tests for async task orchestration and retries."""

import subprocess
import sys

from article_factory.database import create_topic
from article_factory.scheduler import get_task, run_pipeline_async


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
