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

    if isinstance(topic, dict):
        topic_name = topic.get("topic")
        created_at = topic.get("created_at")
    else:
        topic_name = getattr(topic, "topic", None)
        created_at = getattr(topic, "created_at", None)

    if not topic_name:
        raise ValueError(f"Topic {topic_id} missing topic name")
    topic_name = str(topic_name)

    if created_at is None:
        date = datetime.now().strftime("%Y-%m-%d")
    elif isinstance(created_at, str):
        date = created_at[:10]
    elif hasattr(created_at, "strftime"):
        date = created_at.strftime("%Y-%m-%d")
    else:
        date = str(created_at)[:10]

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
    topic = get_topic(topic_id)
    if topic is None:
        raise ValueError(f"Topic {topic_id} not found")

    notebook_id = topic.get("notebook_id") if isinstance(topic, dict) else topic.notebook_id
    if not notebook_id:
        raise ValueError(f"Topic {topic_id} has no notebook_id - run research first")

    client = NotebookLMClientWrapper()
    output_dir = get_output_dir(topic_id)
    image_path = os.path.join(output_dir, "infographic.png")

    if os.path.exists(image_path):
        logger.info(f"Infographic already exists: {image_path}")
        return image_path

    # generate_infographic handles triggering + polling until COMPLETED
    result = await client.generate_infographic(notebook_id)
    task_id = result["task_id"]

    await client.download_infographic(notebook_id, image_path)

    logger.info(f"Infographic generated for topic {topic_id}: {image_path}")
    return image_path

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
