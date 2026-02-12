"""Task scheduler and async pipeline orchestrator."""

import asyncio
import uuid
from datetime import datetime
from typing import Optional, List

from article_factory.database import get_db_session
from article_factory.models import Task, TaskStatus, Topic, TopicStatus
from article_factory.notifications import notify_progress, notify_complete, notify_error, notify_cancelled


def generate_task_id() -> str:
    """Generate a unique task ID (UUID)."""
    return str(uuid.uuid4())


def create_task(topic_id: int, output_dir: str = None, prompt: str = None, prompt_file: str = None) -> str:
    """Create a new task with PENDING status.
    
    Args:
        topic_id: The topic ID to process
        output_dir: Optional custom output directory
        prompt: Optional inline prompt for article generation
        prompt_file: Optional path to prompt file
        
    Returns:
        task_id (UUID string)
    """
    with get_db_session() as session:
        task = Task(
            id=generate_task_id(),
            topic_id=topic_id,
            status=TaskStatus.PENDING,
            current_stage="PENDING",
            progress_percent=0,
            output_dir=output_dir,
            prompt=prompt,
            prompt_file=prompt_file,
        )
        session.add(task)
        session.flush()
        task_id = task.id
        return task_id


def get_task(task_id: str) -> Optional[dict]:
    """Get a task by ID.
    
    Args:
        task_id: The task ID (UUID)
        
    Returns:
        Task dict or None
    """
    with get_db_session() as session:
        task = session.query(Task).filter(Task.id == task_id).first()
        if task:
            return {
                "id": task.id,
                "topic_id": task.topic_id,
                "status": task.status.value if task.status else None,
                "current_stage": task.current_stage,
                "progress_percent": task.progress_percent,
                "error_message": task.error_message,
                "output_dir": task.output_dir,
                "prompt": task.prompt,
                "prompt_file": task.prompt_file,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            }
        return None


def get_all_tasks() -> List[dict]:
    """Get all tasks ordered by created_at descending.
    
    Returns:
        List of Task dicts
    """
    with get_db_session() as session:
        tasks = session.query(Task).order_by(Task.created_at.desc()).all()
        return [
            {
                "id": task.id,
                "topic_id": task.topic_id,
                "status": task.status.value if task.status else None,
                "current_stage": task.current_stage,
                "progress_percent": task.progress_percent,
                "error_message": task.error_message,
                "output_dir": task.output_dir,
                "prompt": task.prompt,
                "prompt_file": task.prompt_file,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            }
            for task in tasks
        ]


def update_task_progress(
    task_id: str,
    stage: TaskStatus,
    progress_percent: int,
    message: str = None,
) -> Optional[Task]:
    """Update task progress and status.
    
    Args:
        task_id: The task ID
        stage: The new pipeline stage
        progress_percent: Progress percentage (0-100)
        message: Optional progress message
        
    Returns:
        Updated Task object or None
    """
    with get_db_session() as session:
        task = session.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = stage
            task.current_stage = stage.value
            task.progress_percent = progress_percent
            task.updated_at = datetime.utcnow()
            if message:
                task.error_message = message
            session.flush()
            # Send progress notification
            notify_progress(task_id, stage.value, progress_percent, message)
            return task
        return None


def cancel_task(task_id: str) -> bool:
    """Cancel a pending or running task.
    
    Args:
        task_id: The task ID
        
    Returns:
        True if cancelled, False if already completed or not found
    """
    with get_db_session() as session:
        task = session.query(Task).filter(Task.id == task_id).first()
        if task and task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            task.status = TaskStatus.CANCELLED
            task.current_stage = "CANCELLED"
            task.updated_at = datetime.utcnow()
            session.flush()
            return True
        return False


def run_pipeline_async(
    topic_id: int,
    prompt: str = None,
    prompt_file: str = None,
    output_dir: str = None,
) -> str:
    """Start async pipeline for a topic, return task_id immediately.
    
    This function creates a task and schedules it for background execution.
    It returns immediately without waiting for the pipeline to complete.
    
    Args:
        topic_id: The topic ID to process
        prompt: Optional inline prompt for article generation
        prompt_file: Optional path to prompt file
        output_dir: Optional custom output directory
        
    Returns:
        task_id (UUID string)
    """
    task_id = create_task(topic_id, output_dir, prompt, prompt_file)
    
    # Schedule async execution in a background thread
    import threading
    thread = threading.Thread(target=lambda: asyncio.run(_execute_pipeline(task_id)), daemon=True)
    thread.start()
    
    return task_id


PIPELINE_STAGES = {
    TaskStatus.PENDING: 0,
    TaskStatus.NOTEBOOK_CREATED: 10,
    TaskStatus.RESEARCH_TRIGGERED: 20,
    TaskStatus.RESEARCH_COMPLETED: 50,
    TaskStatus.SYNTHESIS_DONE: 60,
    TaskStatus.ARTICLE_DONE: 80,
    TaskStatus.MEDIA_DONE: 90,
    TaskStatus.COMPLETED: 100,
}


async def _execute_pipeline(task_id: str) -> None:
    """Execute the full pipeline for a task.
    
    This runs in the background and updates progress as it goes.
    
    Args:
        task_id: The task ID to execute
    """
    try:
        task = get_task(task_id)
        if not task:
            update_task_progress(task_id, TaskStatus.FAILED, 0, f"Task {task_id} not found")
            return
        
        topic_id = task["topic_id"]
        output_dir = task.get("output_dir")
        task_prompt = task.get("prompt")
        task_prompt_file = task.get("prompt_file")
        
        # Get topic info
        with get_db_session() as session:
            from article_factory.database import get_topic as db_get_topic
            topic = db_get_topic(topic_id)
        
        if not topic:
            update_task_progress(task_id, TaskStatus.FAILED, 0, f"Topic {topic_id} not found")
            return
        
        topic_name = topic.get("topic") if isinstance(topic, dict) else topic.topic
        topic_prompt = topic.get("prompt") if isinstance(topic, dict) else topic.prompt
        
        # Stage: NOTEBOOK_CREATED
        update_task_progress(task_id, TaskStatus.NOTEBOOK_CREATED, 10, "Creating notebook")
        
        from article_factory.notebooks import create_notebook_for_topic
        notebook_id = await create_notebook_for_topic(topic_id, topic_name, topic_prompt or "")
        
        # Stage: RESEARCH_TRIGGERED
        update_task_progress(task_id, TaskStatus.RESEARCH_TRIGGERED, 20, "Starting research")
        
        from article_factory.notebooks import trigger_deep_research
        task_id_research = await trigger_deep_research(topic_id, notebook_id, topic_prompt or "")
        
        # Stage: RESEARCH_COMPLETED
        update_task_progress(task_id, TaskStatus.RESEARCH_COMPLETED, 50, "Research in progress")
        
        from article_factory.notebooks import wait_for_research_completion
        await wait_for_research_completion(notebook_id, task_id_research)
        
        # Stage: SYNTHESIS_DONE
        update_task_progress(task_id, TaskStatus.SYNTHESIS_DONE, 60, "Generating synthesis")
        
        from article_factory.research import generate_synthesis
        from article_factory.database import get_topic
        from slugify import slugify as slugify_func
        topic_data = get_topic(topic_id)
        topic_name = topic_data.get("topic", "unknown") if topic_data else "unknown"
        topic_slug = slugify_func(topic_name)
        synthesis = await generate_synthesis(notebook_id, topic_slug)
        
        article_text = None
        
        # Stage: ARTICLE_DONE
        if task_prompt or task_prompt_file:
            try:
                update_task_progress(task_id, TaskStatus.ARTICLE_DONE, 80, "Generating article")
                from article_factory.article import generate_article
                article_text = await generate_article(topic_id, task_prompt, task_prompt_file)
            except Exception as e:
                print(f"Warning: Article generation failed (skipping): {e}")
                article_text = None
        
        # Stage: MEDIA_DONE
        update_task_progress(task_id, TaskStatus.MEDIA_DONE, 90, "Generating media")
        
        # Generate infographic
        try:
            from article_factory.media import generate_infographic
            await generate_infographic(topic_id)
        except Exception as e:
            print(f"Warning: Infographic generation failed: {e}")
        
        # Generate audio
        try:
            from article_factory.audio import generate_audio_briefing
            await generate_audio_briefing(topic_id)
        except Exception as e:
            print(f"Warning: Audio generation failed: {e}")
        
        # Export all artifacts
        update_task_progress(task_id, TaskStatus.COMPLETED, 100, "Exporting artifacts")
        
        from article_factory.output import export_all_artifacts
        export_all_artifacts(topic_id, article_text, synthesis)
        
        notify_complete(task_id, output_dir or get_default_output_dir(topic_id))
        
    except asyncio.CancelledError:
        update_task_progress(task_id, TaskStatus.CANCELLED, 0, "Task cancelled")
        notify_cancelled(task_id)
        
    except Exception as e:
        update_task_progress(task_id, TaskStatus.FAILED, 0, str(e))
        notify_error(task_id, str(e))


def get_default_output_dir(topic_id: int) -> str:
    """Get default output directory for a topic."""
    from article_factory.database import get_topic
    topic = get_topic(topic_id)
    if topic:
        topic_name = topic.get("topic") if isinstance(topic, dict) else topic.topic
        date = topic.get("created_at", "")[:10] if topic.get("created_at") else "unknown"
        from slugify import slugify as _slugify
        slug = _slugify(topic_name)
        return f"{date}__{slug}"
    return f"topic-{topic_id}"
