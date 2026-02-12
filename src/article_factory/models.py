"""SQLAlchemy models for Article Factory."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, DateTime, Enum as SQLEnum, 
    create_engine, event
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.pool import QueuePool

Base = declarative_base()


class TopicStatus(str, Enum):
    """Topic processing status state machine."""
    NEW = "NEW"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Topic(Base):
    """Topic entity for managing article writing tasks."""
    
    __tablename__ = "topics"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core fields
    topic = Column(String, nullable=False, unique=False)
    prompt = Column(String, nullable=False)
    
    # State machine status
    status = Column(
        SQLEnum(TopicStatus, name="topic_status", create_constraint=False),
        default=TopicStatus.NEW,
        nullable=False
    )
    
    # NotebookLM tracking
    notebook_id = Column(String, nullable=True)
    artifact_ids = Column(String, nullable=True)  # JSON string of artifact IDs
    
    # Retry tracking
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<Topic(id={self.id}, topic='{self.topic}', status={self.status})>"
    
    # State machine transitions
    def transition_to(self, new_status: TopicStatus) -> bool:
        """Validate and perform state transition.
        
        Valid transitions:
        - NEW -> PENDING (when enqueued for processing)
        - PENDING -> PROCESSING (when work starts)
        - PROCESSING -> COMPLETED (on success)
        - PROCESSING -> FAILED (on error, increments retry_count)
        - FAILED -> PENDING (on retry, increments retry_count)
        """
        valid_transitions = {
            TopicStatus.NEW: [TopicStatus.PENDING],
            TopicStatus.PENDING: [TopicStatus.PROCESSING],
            TopicStatus.PROCESSING: [TopicStatus.COMPLETED, TopicStatus.FAILED],
            TopicStatus.FAILED: [TopicStatus.PENDING],
            TopicStatus.COMPLETED: [],  # Terminal state
        }
        
        if new_status in valid_transitions.get(self.status, []):
            self.status = new_status
            return True
        return False
    
    def can_enqueue(self) -> bool:
        """Check if topic can be enqueued for processing."""
        return self.status == TopicStatus.NEW
    
    def can_start_processing(self) -> bool:
        """Check if topic can start processing."""
        return self.status == TopicStatus.PENDING
    
    def can_retry(self) -> bool:
        """Check if topic can be retried (max retries not exceeded)."""
        return self.status == TopicStatus.FAILED and self.retry_count < 3
    
    def increment_retry(self) -> None:
        """Increment retry count atomically."""
        self.retry_count += 1
    
    def set_notebook_id(self, notebook_id: str) -> None:
        """Set the NotebookLM notebook ID."""
        self.notebook_id = notebook_id
    
    def add_artifact(self, artifact_id: str) -> None:
        """Append artifact ID to artifact_ids list."""
        import json
        current_ids = json.loads(self.artifact_ids) if self.artifact_ids else []
        if artifact_id not in current_ids:
            current_ids.append(artifact_id)
            self.artifact_ids = json.dumps(current_ids)
    
    def to_dict(self) -> dict:
        """Convert topic to dictionary for serialization."""
        return {
            "id": self.id,
            "topic": self.topic,
            "prompt": self.prompt,
            "status": self.status.value if self.status else None,
            "notebook_id": self.notebook_id,
            "artifact_ids": self.artifact_ids,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
