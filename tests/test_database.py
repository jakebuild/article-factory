"""Database helper tests for CRUD, status transitions, and concurrency."""

import asyncio

import pytest

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
    completed_state = get_topic(completed_id)
    assert completed_state is not None
    assert completed_state["status"] == TopicStatus.PENDING.value

    assert update_status(completed_id, TopicStatus.PROCESSING) is not None
    completed_state = get_topic(completed_id)
    assert completed_state is not None
    assert completed_state["status"] == TopicStatus.PROCESSING.value

    assert update_status(completed_id, TopicStatus.COMPLETED) is not None
    completed_state = get_topic(completed_id)
    assert completed_state is not None
    assert completed_state["status"] == TopicStatus.COMPLETED.value

    failed_topic = create_topic(
        topic="DB-02 failed path",
        prompt="Exercise PROCESSING->FAILED",
    )

    assert failed_topic is not None
    failed_id = failed_topic["id"]

    assert update_status(failed_id, TopicStatus.PENDING) is not None
    assert update_status(failed_id, TopicStatus.PROCESSING) is not None
    failed_state = get_topic(failed_id)
    assert failed_state is not None
    assert failed_state["status"] == TopicStatus.PROCESSING.value

    assert update_status(failed_id, TopicStatus.FAILED) is not None
    failed_state = get_topic(failed_id)
    assert failed_state is not None
    assert failed_state["status"] == TopicStatus.FAILED.value


def test_database_unknown_topic_returns_none():
    assert get_topic(999_999) is None


@pytest.mark.asyncio
async def test_database_concurrent_async_operations_persist_without_locks():
    async def create_and_progress(index: int) -> tuple[int, str]:
        created = create_topic(
            f"DB-04 topic {index}",
            f"Concurrent prompt {index}",
        )
        assert created is not None
        topic_id = created["id"]
        await asyncio.sleep(0)

        pending_result = update_status(topic_id, TopicStatus.PENDING)
        assert pending_result is not None
        await asyncio.sleep(0)

        processing_result = update_status(topic_id, TopicStatus.PROCESSING)
        assert processing_result is not None
        await asyncio.sleep(0)

        final_status = TopicStatus.COMPLETED if index % 2 == 0 else TopicStatus.FAILED
        final_result = update_status(topic_id, final_status)
        assert final_result is not None

        persisted = get_topic(topic_id)
        assert persisted is not None
        return topic_id, persisted["status"]

    results = await asyncio.gather(*(create_and_progress(i) for i in range(8)))

    assert len(results) == 8

    completed_ids = []
    failed_ids = []
    for topic_id, status in results:
        if status == TopicStatus.COMPLETED.value:
            completed_ids.append(topic_id)
        elif status == TopicStatus.FAILED.value:
            failed_ids.append(topic_id)

    assert completed_ids
    assert failed_ids

    for topic_id in completed_ids:
        persisted = get_topic(topic_id)
        assert persisted is not None
        assert persisted["status"] == TopicStatus.COMPLETED.value

    for topic_id in failed_ids:
        persisted = get_topic(topic_id)
        assert persisted is not None
        assert persisted["status"] == TopicStatus.FAILED.value
