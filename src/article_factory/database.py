"""SQLite database module with crash recovery support for Article Factory."""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Generator, List, Optional

from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from article_factory.models import Base, Topic, TopicStatus

# Database configuration
DEFAULT_DB_PATH = "article_factory.db"
WAL_MODE_ENABLED = True


def get_database_url() -> str:
    """Get database URL, checking XDG data dir and fallback to default."""
    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        db_path = os.path.join(xdg_data, "article_factory.db")
        os.makedirs(xdg_data, exist_ok=True)
        return f"sqlite:///{db_path}"
    
    # Default to current directory
    db_path = DEFAULT_DB_PATH
    return f"sqlite:///{db_path}"


# Create engine with WAL mode for concurrent async access
def create_database_engine():
    """Create SQLAlchemy engine with WAL mode enabled."""
    database_url = get_database_url()
    
    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # Enable connection health checks
        echo=False,
    )
    
    # Enable WAL mode for concurrent access
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    return engine


# Global engine instance
_engine = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        _engine = create_database_engine()
    return _engine


# Session factory
SessionLocal = None


def get_session_factory():
    """Get or create the session factory."""
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=get_engine()
        )
    return SessionLocal


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    SessionFactory = get_session_factory()
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database():
    """Initialize database and create tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    return engine


# CRUD Operations

def create_topic(topic: str, prompt: str) -> Topic:
    """Create a new topic with idempotent handling.
    
    Args:
        topic: User-provided topic name
        prompt: User-provided writing prompt
        
    Returns:
        The created Topic object
    """
    with get_db_session() as session:
        # Check for existing topic with same name
        existing = session.query(Topic).filter(Topic.topic == topic).first()
        if existing:
            # Return existing topic (idempotent operation)
            return existing
        
        new_topic = Topic(topic=topic, prompt=prompt)
        session.add(new_topic)
        session.flush()  # Get ID without committing
        return new_topic


def get_topic(id: int) -> Optional[Topic]:
    """Retrieve a topic by ID."""
    with get_db_session() as session:
        return session.query(Topic).filter(Topic.id == id).first()


def get_all_topics() -> List[Topic]:
    """Retrieve all topics ordered by created_at descending."""
    with get_db_session() as session:
        return session.query(Topic).order_by(Topic.created_at.desc()).all()


def update_status(id: int, new_status: TopicStatus) -> Optional[Topic]:
    """Update topic status with transition validation.
    
    Args:
        id: Topic ID
        new_status: Desired new status
        
    Returns:
        Updated Topic or None if not found
    """
    with get_db_session() as session:
        topic = session.query(Topic).filter(Topic.id == id).first()
        if not topic:
            return None
        
        if topic.transition_to(new_status):
            return topic
        return None


def increment_retry(id: int) -> Optional[Topic]:
    """Increment retry count atomically."""
    with get_db_session() as session:
        topic = session.query(Topic).filter(Topic.id == id).first()
        if not topic:
            return None
        
        topic.increment_retry()
        session.flush()
        return topic


def set_notebook_id(id: int, notebook_id: str) -> Optional[Topic]:
    """Set the NotebookLM notebook ID for a topic."""
    with get_db_session() as session:
        topic = session.query(Topic).filter(Topic.id == id).first()
        if not topic:
            return None
        
        topic.set_notebook_id(notebook_id)
        session.flush()
        return topic


def add_artifact(id: int, artifact_id: str) -> Optional[Topic]:
    """Add an artifact ID to a topic."""
    with get_db_session() as session:
        topic = session.query(Topic).filter(Topic.id == id).first()
        if not topic:
            return None
        
        topic.add_artifact(artifact_id)
        session.flush()
        return topic


def get_pending_topics() -> List[Topic]:
    """Get all topics ready for processing (PENDING status)."""
    with get_db_session() as session:
        return session.query(Topic).filter(
            Topic.status == TopicStatus.PENDING
        ).order_by(Topic.created_at.asc()).all()


def get_topics_by_status(status: TopicStatus) -> List[Topic]:
    """Get all topics with a specific status."""
    with get_db_session() as session:
        return session.query(Topic).filter(
            Topic.status == status
        ).order_by(Topic.created_at.desc()).all()


# Crash Recovery Operations

def recover_crashed_topics() -> int:
    """Recover topics that were in PROCESSING state (orphaned work).
    
    This should be called on startup to handle topics that were
    being processed when the application crashed.
    
    Returns:
        Number of topics recovered
    """
    with get_db_session() as session:
        # Find all PROCESSING topics
        crashed_topics = session.query(Topic).filter(
            Topic.status == TopicStatus.PROCESSING
        ).all()
        
        recovered_count = 0
        for topic in crashed_topics:
            # Set back to PENDING for retry
            topic.status = TopicStatus.PENDING
            topic.updated_at = datetime.utcnow()
            recovered_count += 1
        
        session.flush()
        return recovered_count


def get_topic_stats() -> dict:
    """Get database statistics for monitoring."""
    with get_db_session() as session:
        stats = {}
        
        # Count by status
        for status in TopicStatus:
            count = session.query(Topic).filter(
                Topic.status == status
            ).count()
            stats[status.value] = count
        
        stats['total'] = sum(stats.values())
        
        # Total retry count
        total_retries = session.query(Topic).with_entities(
            Topic.retry_count
        ).all()
        stats['total_retries'] = sum(r[0] for r in total_retries)
        
        return stats


# Initialize database on module import
# This creates article_factory.db when the module is first imported
try:
    init_database()
    # Attempt crash recovery on startup
    # This handles any orphaned PROCESSING topics from previous runs
    try:
        recovered = recover_crashed_topics()
        if recovered > 0:
            print(f"Recovered {recovered} crashed topics on startup")
    except Exception:
        # Database might not exist yet on first import
        pass
except Exception as e:
    # Delay initialization if database is locked or doesn't exist
    # This can happen during parallel imports
    pass


def shutdown_engine():
    """Properly shutdown the database engine (call on app exit)."""
    global _engine, SessionLocal
    if _engine:
        _engine.dispose()
        _engine = None
        SessionLocal = None
