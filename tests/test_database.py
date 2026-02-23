"""Database helper tests for CRUD, status transitions, and concurrency."""

import asyncio

from article_factory.database import create_topic, get_topic, update_status
from article_factory.models import TopicStatus


def test_database_crud_create_and_get_topic():
    created = create_topic(
        topic="DB-01 topic",
        prompt="Validate topic persistence",
    )

    assert created is not None
    created_id = created["id"]

    fetched = get_topic(created_id)

    assert fetched is not None
    assert fetched["id"] == created_id
    assert fetched["topic"] == "DB-01 topic"
    assert fetched["prompt"] == "Validate topic persistence"
    assert fetched["status"] == TopicStatus.NEW.value


def test_database_transition_persistence_paths():
    completed_topic = create_topic(
        topic="DB-02 completed path",
        prompt="Exercise NEW->PENDING->PROCESSING->COMPLETED",
    )

    assert completed_topic is not None
    completed_id = completed_topic["id"]

    assert update_status(completed_id, TopicStatus.PENDING) is not None
    assert get_topic(completed_id)["status"] == TopicStatus.PENDING.value

    assert update_status(completed_id, TopicStatus.PROCESSING) is not None
    assert get_topic(completed_id)["status"] == TopicStatus.PROCESSING.value

    assert update_status(completed_id, TopicStatus.COMPLETED) is not None
    assert get_topic(completed_id)["status"] == TopicStatus.COMPLETED.value

    failed_topic = create_topic(
        topic="DB-02 failed path",
        prompt="Exercise PROCESSING->FAILED",
    )

    assert failed_topic is not None
    failed_id = failed_topic["id"]

    assert update_status(failed_id, TopicStatus.PENDING) is not None
    assert update_status(failed_id, TopicStatus.PROCESSING) is not None
    assert get_topic(failed_id)["status"] == TopicStatus.PROCESSING.value

    assert update_status(failed_id, TopicStatus.FAILED) is not None
    assert get_topic(failed_id)["status"] == TopicStatus.FAILED.value


def test_database_unknown_topic_returns_none():
    assert get_topic(999_999) is None
