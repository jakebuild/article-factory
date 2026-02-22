"""Shared pytest fixtures for test infrastructure."""

from pathlib import Path
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

import article_factory.database as db_module
from article_factory.models import Base, Topic, TopicStatus
from article_factory.notebook_lm import NotebookLMClientWrapper


@pytest.fixture
def db_session(monkeypatch):
    """Isolated in-memory SQLite session pre-seeded with two topics."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    monkeypatch.setattr(db_module, "_engine", engine)
    monkeypatch.setattr(db_module, "SessionLocal", Session)

    seed_session = Session()
    t1 = Topic(
        topic="Python Async",
        prompt="Write about async Python",
        status=TopicStatus.NEW,
    )
    t2 = Topic(
        topic="AI Safety",
        prompt="Write about AI safety",
        status=TopicStatus.PROCESSING,
    )
    seed_session.add_all([t1, t2])
    seed_session.commit()
    seed_session.close()

    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def mock_nlm_client():
    """Return AsyncMock-backed NotebookLM client wrapper for tests."""
    client = MagicMock(spec=NotebookLMClientWrapper)
    client.create_notebook = AsyncMock(return_value="notebook-test-id")
    client.get_notebook = AsyncMock(return_value={"id": "notebook-test-id", "title": "Test"})
    client.start_research = AsyncMock(return_value={"task_id": "research-task-id"})
    client.poll_research = AsyncMock(
        return_value={
            "status": "completed",
            "sources": [{"title": "Source 1", "url": "https://example.com"}],
        }
    )
    client.generate_audio = AsyncMock(return_value={"task_id": "audio-task-id"})
    client.wait_for_completion = AsyncMock(
        return_value={
            "status": "completed",
            "url": "https://example.com/audio.mp3",
            "error": None,
        }
    )
    client.download_audio = AsyncMock(return_value="/tmp/audio.mp3")
    client.import_sources = AsyncMock(return_value=[{"id": "src-1"}])
    client.list_sources = AsyncMock(return_value=[{"id": "src-1", "title": "Source 1"}])
    client.generate_infographic = AsyncMock(return_value={"task_id": "infographic-task-id"})
    client.download_infographic = AsyncMock(return_value="/tmp/infographic.png")
    return client
