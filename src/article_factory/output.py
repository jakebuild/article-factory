"""Output/export module for artifact management and batch processing."""

import json
import logging
import os
from datetime import datetime
from typing import Optional

from article_factory.database import get_topic, get_all_topics
from article_factory.models import TopicStatus

logger = logging.getLogger(__name__)

def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    import sys
    slugify_mod = sys.modules.get('slugify') or __import__('slugify')
    _slugify = getattr(slugify_mod, 'slugify', None) or __import__('slugify').slugify
    return _slugify(text, max_length=80)

def get_output_dir(topic_id: int) -> str:
    """Get output directory for a topic.
    
    Creates directory if it doesn't exist.
    
    Args:
        topic_id: Topic database ID
        
    Returns:
        Path to output directory (output/YYYY-MM-DD/topic-slug/)
    """
    topic = get_topic(topic_id)
    if topic is None:
        raise ValueError(f"Topic {topic_id} not found")
    
    topic_name = topic.get("topic") or ""
    date = topic.get("created_at", "")[:10] if topic.get("created_at") else datetime.now().strftime("%Y-%m-%d")
    slug = slugify(topic_name)
    dir_path = os.path.join("output", f"{date}__{slug}")
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def export_article(topic_id: int, article_text: str, output_dir: str) -> str:
    """Export article to file.
    
    Args:
        topic_id: Topic database ID
        article_text: Article content
        output_dir: Output directory path
        
    Returns:
        Path to saved article file
    """
    filepath = os.path.join(output_dir, "article.md")
    with open(filepath, 'w') as f:
        f.write(article_text)
    logger.info(f"Article exported: {filepath}")
    return filepath

def export_research_synthesis(topic_id: int, synthesis: str, output_dir: str) -> str:
    """Export research synthesis to file.
    
    Args:
        topic_id: Topic database ID
        synthesis: Research synthesis content
        output_dir: Output directory path
        
    Returns:
        Path to saved synthesis file
    """
    filepath = os.path.join(output_dir, "research_synthesis.md")
    with open(filepath, 'w') as f:
        f.write(synthesis)
    logger.info(f"Research synthesis exported: {filepath}")
    return filepath

def export_infographic(topic_id: int, image_path: str, output_dir: str) -> str:
    """Export infographic image to output directory.
    
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
    logger.info(f"Infographic exported: {final_path}")
    return final_path

def export_audio_briefing(topic_id: int, audio_path: str, output_dir: str) -> str:
    """Export audio briefing to output directory.
    
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
    logger.info(f"Audio briefing exported: {final_path}")
    return final_path

def export_metadata(topic_id: int, metadata: dict, output_dir: str) -> str:
    """Export metadata JSON to output directory.
    
    Args:
        topic_id: Topic database ID
        metadata: Metadata dictionary
        output_dir: Output directory path
        
    Returns:
        Path to saved metadata file
    """
    filepath = os.path.join(output_dir, "metadata.json")
    with open(filepath, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata exported: {filepath}")
    return filepath

def export_all_artifacts(topic_id: int, article_text: str = None, synthesis: str = None, 
                         image_path: str = None, audio_path: str = None) -> dict:
    """Export all generated artifacts to structured output directory.
    
    Args:
        topic_id: Topic database ID
        article_text: Optional article content
        synthesis: Optional research synthesis
        image_path: Optional infographic path
        audio_path: Optional audio briefing path
        
    Returns:
        Dictionary with all exported file paths
    """
    topic = get_topic(topic_id)
    if topic is None:
        raise ValueError(f"Topic {topic_id} not found")
    
    output_dir = get_output_dir(topic_id)
    
    exported = {
        "topic_id": topic_id,
        "output_dir": output_dir,
        "exported_at": datetime.utcnow().isoformat(),
    }
    
    # Export each artifact if provided
    if article_text:
        exported["article"] = export_article(topic_id, article_text, output_dir)
    
    if synthesis:
        exported["research_synthesis"] = export_research_synthesis(topic_id, synthesis, output_dir)
    
    if image_path:
        exported["infographic"] = export_infographic(topic_id, image_path, output_dir)
    
    if audio_path:
        exported["audio_briefing"] = export_audio_briefing(topic_id, audio_path, output_dir)
    
    # Always export metadata
    metadata = {
        "topic_id": topic_id,
        "topic": topic.get("topic") if isinstance(topic, dict) else topic.topic,
        "status": topic.get("status") if isinstance(topic, dict) else topic.status.value,
        "notebook_id": topic.get("notebook_id"),
        "exported_at": exported["exported_at"],
        "files": {k: v for k, v in exported.items() if k in ["article", "research_synthesis", "infographic", "audio_briefing"]},
    }
    exported["metadata"] = export_metadata(topic_id, metadata, output_dir)
    
    logger.info(f"All artifacts exported for topic {topic_id}")
    return exported

def get_topic_output_path(topic_id: int, filename: str) -> str:
    """Get path to specific file in topic's output directory.
    
    Args:
        topic_id: Topic database ID
        filename: Name of file (e.g., 'article.md', 'metadata.json')
        
    Returns:
        Full path to file
    """
    output_dir = get_output_dir(topic_id)
    return os.path.join(output_dir, filename)

# Batch processing

def process_topics_from_file(
    filepath: str,
    prompt: Optional[str] = None,
    prompt_file: Optional[str] = None,
    max_retries: int = 2,
) -> list:
    """Process multiple topics from a file.
    
    Reads topic IDs from file (one per line) and processes each sequentially.
    
    Args:
        filepath: Path to file containing topic IDs (one per line)
        prompt: Optional inline prompt for article generation
        prompt_file: Optional path to prompt file
        max_retries: Maximum retries per failed operation
        
    Returns:
        List of processing results for each topic
    """
    if not os.path.exists(filepath):
        raise ValueError(f"Topics file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        topic_ids = [line.strip() for line in f if line.strip()]
    
    results = []
    for topic_id_str in topic_ids:
        try:
            topic_id = int(topic_id_str)
            result = process_topic(topic_id, prompt, prompt_file, max_retries)
            results.append({"topic_id": topic_id, "status": "success", **result})
        except Exception as e:
            results.append({"topic_id": topic_id_str, "status": "error", "error": str(e)})
    
    return results

def process_topic(
    topic_id: int,
    prompt: Optional[str] = None,
    prompt_file: Optional[str] = None,
    max_retries: int = 2,
) -> dict:
    """Process a single topic: generate article, media, and export.
    
    Orchestrates full topic processing workflow.
    
    Args:
        topic_id: Topic database ID
        prompt: Optional inline prompt for article generation
        prompt_file: Optional path to prompt file
        max_retries: Maximum retries per failed operation
        
    Returns:
        Dictionary with processing result
    """
    from article_factory.article import generate_article
    from article_factory.media import generate_infographic
    from article_factory.audio import generate_audio_briefing
    
    topic = get_topic(topic_id)
    if topic is None:
        raise ValueError(f"Topic {topic_id} not found")
    
    result = {
        "topic_id": topic_id,
        "article": None,
        "infographic": None,
        "audio": None,
        "exported": None,
    }
    
    retries = 0
    while retries < max_retries:
        try:
            # Generate article if prompt provided
            if prompt or prompt_file:
                article_text = generate_article(topic_id, prompt, prompt_file)
                result["article"] = article_text
            
            # Generate infographic
            try:
                infographic = generate_infographic(topic_id)
                result["infographic"] = infographic
            except Exception as e:
                logger.warning(f"Infographic generation skipped: {e}")
            
            # Generate audio briefing
            try:
                audio = generate_audio_briefing(topic_id)
                result["audio"] = audio
            except Exception as e:
                logger.warning(f"Audio briefing generation skipped: {e}")
            
            # Export all artifacts
            exported = export_all_artifacts(
                topic_id,
                article_text=result.get("article"),
                image_path=result.get("infographic"),
                audio_path=result.get("audio"),
            )
            result["exported"] = exported
            
            return result
            
        except Exception as e:
            retries += 1
            logger.error(f"Processing failed for topic {topic_id} (attempt {retries}/{max_retries}): {e}")
            if retries >= max_retries:
                raise
    
    return result
