"""Media generation module for infographics and images."""

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
    from slugify import slugify as _slugify
    return _slugify(text, max_length=80)

def get_output_dir(topic_id: int) -> str:
    """Get output directory for a topic."""
    topic = get_topic(topic_id)
    if topic is None:
        raise ValueError(f"Topic {topic_id} not found")
    topic_name = topic.get("topic") or topic.topic if hasattr(topic, "topic") else ""
    date = topic.get("created_at", "")[:10] if topic.get("created_at") else datetime.now().strftime("%Y-%m-%d")
    slug = slugify(topic_name)
    dir_path = os.path.join("output", f"{date}__{slug}")
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

async def get_notebook_content(notebook_id: str) -> str:
    """Get notebook content/synthesis for media generation context."""
    client = NotebookLMClientWrapper()
    try:
        async with await client.get_client() as api_client:
            notebook = await api_client.notebooks.get(notebook_id)
            # Return title or synthesis content
            return getattr(notebook, 'title', '') or getattr(notebook, 'summary', '') or str(notebook)
    except Exception as e:
        logger.error(f"Failed to get notebook content: {e}")
        return ""

async def generate_infographic(topic_id: int) -> str:
    """Generate infographic image from notebook context.
    
    Args:
        topic_id: Database ID of the topic
        
    Returns:
        Path to generated infographic image
    """
    # Load topic to get notebook_id
    topic = get_topic(topic_id)
    if topic is None:
        raise ValueError(f"Topic {topic_id} not found")
    
    notebook_id = topic.get("notebook_id") if isinstance(topic, dict) else topic.notebook_id
    if not notebook_id:
        raise ValueError(f"Topic {topic_id} has no notebook_id - run research first")
    
    # Update status to PROCESSING for media generation
    async with get_db_session() as session:
        await update_status(session, topic_id, TopicStatus.PROCESSING)
    
    # Get notebook content for context
    content = await get_notebook_content(notebook_id)
    
    # Build prompt for infographic generation
    infographic_prompt = f"""Generate an infographic summarizing the key points from this research. 
The infographic should be informative, visually clear, and capture the main findings.

Research content:
{content[:2000]}..."""
    
    client = NotebookLMClientWrapper()
    output_dir = get_output_dir(topic_id)
    
    try:
        await rate_limiter.acquire()
        try:
            async with circuit_breaker.call:
                async with await client.get_client() as api_client:
                    # Generate infographic via NotebookLM API
                    result = await api_client.artifacts.generate_image(
                        notebook_id=notebook_id,
                        instructions=infographic_prompt,
                    )
                    task_id = result.task_id if hasattr(result, 'task_id') else result.get('task_id')
                    
                    # Wait for completion
                    completion = await client.wait_for_completion(notebook_id, task_id)
                    
                    # Get artifact and download
                    artifact_id = getattr(completion, 'artifact_id', None) or completion.get('artifact_id')
                    if artifact_id:
                        image_path = os.path.join(output_dir, "infographic.png")
                        await client.download_audio(notebook_id, image_path, artifact_id)
                    else:
                        raise ValueError("No artifact ID returned from image generation")
        finally:
            rate_limiter.release()
    
    except Exception as e:
        logger.error(f"Infographic generation failed for topic {topic_id}: {e}")
        async with get_db_session() as session:
            await update_status(session, topic_id, TopicStatus.FAILED)
        raise RuntimeError(f"Infographic generation failed: {e}")
    
    logger.info(f"Infographic generated for topic {topic_id}")
    return f"{output_dir}/infographic.png"

def save_infographic(topic_id: int, image_path: str, output_dir: str) -> str:
    """Save infographic to output directory.
    
    Args:
        topic_id: Topic database ID
        image_path: Path to generated image
        output_dir: Output directory path
        
    Returns:
        Path to saved infographic
    """
    import shutil
    final_path = os.path.join(output_dir, "infographic.png")
    if os.path.exists(image_path) and image_path != final_path:
        shutil.copy2(image_path, final_path)
    logger.info(f"Infographic saved: {final_path}")
    return final_path
