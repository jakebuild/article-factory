"""Shared pytest fixtures for test infrastructure."""

from pathlib import Path
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
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
    client = MagicMock()
    client.artifacts = MagicMock()
    client.notebooks = MagicMock()
    client.chat = MagicMock()
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

    client.artifacts.generate_report = AsyncMock(return_value=MagicMock(id="artifact-123"))
    client.artifacts.wait_for_completion = AsyncMock(return_value=MagicMock(artifact_id="artifact-456"))
    client.artifacts.export_report = AsyncMock(return_value="# Article\n\nContent...")
    client.notebooks.get = AsyncMock(return_value=MagicMock(sources=[]))
    client.chat.ask = AsyncMock(return_value=MagicMock(answer="Generated article content"))
    return client


@pytest.fixture(autouse=True)
def enforce_mocked_nlm_client(monkeypatch, mock_nlm_client):
    """Route all NotebookLM client construction through shared mock fixture."""
    mock_client_ctx = AsyncMock()
    mock_client_ctx.__aenter__.return_value = mock_nlm_client
    mock_client_ctx.__aexit__.return_value = False

    monkeypatch.setattr(
        NotebookLMClientWrapper,
        "get_client",
        AsyncMock(return_value=mock_client_ctx),
    )


@pytest.fixture(autouse=True)
def enforce_in_memory_db_isolation(db_session):
    """Ensure each test runs with fixture-provided in-memory DB wiring."""
    yield db_session
