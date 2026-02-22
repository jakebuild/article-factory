"""Tests for Topic and Task model helpers."""

import json

from article_factory.models import Task, TaskStatus, Topic, TopicStatus


def test_topic_transition_and_retry_rules():
    topic = Topic(topic="AI", prompt="Write about AI", status=TopicStatus.NEW)

    assert topic.transition_to(TopicStatus.PENDING) is True
    assert topic.status == TopicStatus.PENDING
    assert topic.transition_to(TopicStatus.COMPLETED) is False

    topic.status = TopicStatus.FAILED
    topic.retry_count = 2
    assert topic.can_retry() is True

    topic.increment_retry()
    assert topic.retry_count == 3
    assert topic.can_retry() is False


def test_topic_artifact_and_content_flags_and_to_dict():
    topic = Topic(topic="Python", prompt="Async guide", status=TopicStatus.PROCESSING)
    topic.retry_count_content = 0
    topic.article_generated = 0
    topic.infographic_generated = 0
    topic.audio_generated = 0
    topic.set_notebook_id("nb-123")
    topic.add_artifact("art-1")
    topic.add_artifact("art-1")
    topic.add_artifact("art-2")
    topic.increment_retry_content()
    topic.mark_content_generated("article")
    topic.mark_content_generated("infographic")
    topic.mark_content_generated("audio")

    data = topic.to_dict()

    assert topic.can_start_processing() is False
    assert topic.can_enqueue() is False
    assert json.loads(data["artifact_ids"]) == ["art-1", "art-2"]
    assert data["notebook_id"] == "nb-123"
    assert data["retry_count_content"] == 1
    assert data["article_generated"] is True
    assert data["infographic_generated"] is True
    assert data["audio_generated"] is True
    assert data["status"] == TopicStatus.PROCESSING.value


def test_task_to_dict_serializes_expected_fields():
    task = Task(
        id="task-1",
        topic_id=99,
        status=TaskStatus.RUNNING,
        current_stage="RESEARCH",
        progress_percent=25,
        error_message=None,
        output_dir="output/2026-02-22/topic",
        prompt="write prompt",
        prompt_file=None,
    )

    data = task.to_dict()

    assert data["id"] == "task-1"
    assert data["topic_id"] == 99
    assert data["status"] == TaskStatus.RUNNING.value
    assert data["current_stage"] == "RESEARCH"
    assert data["progress_percent"] == 25
    assert data["output_dir"] == "output/2026-02-22/topic"
    assert data["prompt"] == "write prompt"


def test_seeded_topics_available_via_db_session(db_session):
    topics = db_session.query(Topic).all()
    topic_names = {topic.topic for topic in topics}

    assert len(topics) >= 1
    assert {"Python Async", "AI Safety"}.issubset(topic_names)
