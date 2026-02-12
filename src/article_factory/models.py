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


class TaskStatus(str, Enum):
    """Task pipeline status state machine."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    NOTEBOOK_CREATED = "NOTEBOOK_CREATED"
    RESEARCH_TRIGGERED = "RESEARCH_TRIGGERED"
    RESEARCH_COMPLETED = "RESEARCH_COMPLETED"
    SYNTHESIS_DONE = "SYNTHESIS_DONE"
    ARTICLE_DONE = "ARTICLE_DONE"
    MEDIA_DONE = "MEDIA_DONE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


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
    
    # Content generation tracking
    article_generated = Column(Integer, default=0, nullable=False)  # 0=no, 1=yes
    infographic_generated = Column(Integer, default=0, nullable=False)  # 0=no, 1=yes
    audio_generated = Column(Integer, default=0, nullable=False)  # 0=no, 1=yes
    retry_count_content = Column(Integer, default=0, nullable=False)  # For ERR-03 retry tracking
    
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
    
    def increment_retry_content(self) -> None:
        """Increment content retry count for ERR-03."""
        self.retry_count_content += 1
    
    def mark_content_generated(self, content_type: str) -> None:
        """Mark content type as generated.
        
        Args:
            content_type: One of 'article', 'infographic', 'audio'
        """
        if content_type == 'article':
            self.article_generated = 1
        elif content_type == 'infographic':
            self.infographic_generated = 1
        elif content_type == 'audio':
            self.audio_generated = 1
    
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
            "retry_count_content": self.retry_count_content,
            "article_generated": bool(self.article_generated),
            "infographic_generated": bool(self.infographic_generated),
            "audio_generated": bool(self.audio_generated),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Task(Base):
    """Task entity for async pipeline execution tracking."""
    
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True)  # UUID
    topic_id = Column(Integer, nullable=False)
    status = Column(
        SQLEnum(TaskStatus, name="task_status", create_constraint=False),
        default=TaskStatus.PENDING,
        nullable=False
    )
    current_stage = Column(String, nullable=True)
    progress_percent = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    output_dir = Column(String, nullable=True)
    prompt = Column(String, nullable=True)
    prompt_file = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<Task(id={self.id}, topic_id={self.topic_id}, status={self.status})>"
    
    def to_dict(self) -> dict:
        """Convert task to dictionary for serialization."""
        return {
            "id": self.id,
            "topic_id": self.topic_id,
            "status": self.status.value if self.status else None,
            "current_stage": self.current_stage,
            "progress_percent": self.progress_percent,
            "error_message": self.error_message,
            "output_dir": self.output_dir,
            "prompt": self.prompt,
            "prompt_file": self.prompt_file,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
