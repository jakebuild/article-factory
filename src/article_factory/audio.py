"""Audio generation module for executive audio briefings."""

import logging
import os
from datetime import datetime
from typing import Optional

from article_factory.database import get_db_session, update_status, get_topic
from article_factory.errors import circuit_breaker, rate_limiter
from article_factory.notebook_lm import NotebookLMClientWrapper
from article_factory.models import TopicStatus

logger = logging.getLogger(__name__)

def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    import slugify as _slugify
    return _slugify(text, max_length=80)

def get_output_dir(topic_id: int) -> str:
    """Get output directory for a topic."""
    topic = get_topic(topic_id)
    if topic is None:
        raise ValueError(f"Topic {topic_id} not found")
    topic_name = topic.get("topic") or topic.topic if hasattr(topic, "topic") else ""
    date = topic.get("created_at", "")[:10] if topic.get("created_at") else datetime.now().strftime("%Y-%m-%d")
    slug = slugify(topic_name)
    dir_path = f"{date}__{slug}"
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

async def get_notebook_synthesis(notebook_id: str) -> str:
    """Get notebook synthesis for audio generation context."""
    client = NotebookLMClientWrapper()
    try:
        async with await client.get_client() as api_client:
            notebook = await api_client.notebooks.get(notebook_id)
            return getattr(notebook, 'summary', '') or getattr(notebook, 'title', '') or str(notebook)
    except Exception as e:
        logger.error(f"Failed to get notebook synthesis: {e}")
        return ""

async def generate_audio_briefing(
    topic_id: int,
    min_duration: int = 8,
    max_duration: int = 10,
) -> str:
    """Generate executive audio briefing (8-10 minutes) from notebook content.
    
    Args:
        topic_id: Database ID of the topic
        min_duration: Minimum duration in minutes
        max_duration: Maximum duration in minutes
        
    Returns:
        Path to generated audio file (MP3)
    """
    # Load topic to get notebook_id
    topic = get_topic(topic_id)
    if topic is None:
        raise ValueError(f"Topic {topic_id} not found")
    
    notebook_id = topic.get("notebook_id") if isinstance(topic, dict) else topic.notebook_id
    if not notebook_id:
        raise ValueError(f"Topic {topic_id} has no notebook_id - run research first")
    
    # Update status to PROCESSING for audio generation
    async with get_db_session() as session:
        await update_status(session, topic_id, TopicStatus.PROCESSING)
    
    # Get notebook synthesis for context
    synthesis = await get_notebook_synthesis(notebook_id)
    
    # Build prompt for audio briefing generation
    audio_prompt = f"""Generate an executive audio briefing that is {min_duration}-{max_duration} minutes long.
The briefing should summarize the key findings from the research in a professional, engaging format suitable for podcast/audio consumption.

Research summary:
{synthesis[:3000]}..."""
    
    client = NotebookLMClientWrapper()
    output_dir = get_output_dir(topic_id)
    
    try:
        async with rate_limiter.acquire():
            async with circuit_breaker.call:
                async with await client.get_client() as api_client:
                    # Generate audio via NotebookLM API
                    result = await client.generate_audio(notebook_id, audio_prompt)
                    task_id = result.get("task_id") if isinstance(result, dict) else result.task_id
                    
                    # Wait for completion
                    completion = await client.wait_for_completion(notebook_id, task_id)
                    
                    # Get artifact and download audio
                    artifact_id = getattr(completion, 'artifact_id', None) or completion.get('artifact_id')
                    if artifact_id:
                        audio_path = os.path.join(output_dir, "podcast.mp3")
                        await client.download_audio(notebook_id, audio_path, artifact_id)
                    else:
                        raise ValueError("No artifact ID returned from audio generation")
    
    except Exception as e:
        logger.error(f"Audio briefing generation failed for topic {topic_id}: {e}")
        async with get_db_session() as session:
            await update_status(session, topic_id, TopicStatus.FAILED)
        raise RuntimeError(f"Audio briefing generation failed: {e}")
    
    logger.info(f"Audio briefing generated for topic {topic_id}")
    return f"{output_dir}/podcast.mp3"

def save_audio_briefing(topic_id: int, audio_path: str, output_dir: str) -> str:
    """Save audio briefing to output directory.
    
    Args:
        topic_id: Topic database ID
        audio_path: Path to generated audio
        output_dir: Output directory path
        
    Returns:
        Path to saved audio file
    """
    import shutil
    final_path = os.path.join(output_dir, "podcast.mp3")
    if os.path.exists(audio_path) and audio_path != final_path:
        shutil.copy2(audio_path, final_path)
    logger.info(f"Audio briefing saved: {final_path}")
    return final_path
