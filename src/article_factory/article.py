"""Article generation module with dynamic prompting."""

import json
import logging
import os
import re
from datetime import datetime
from typing import Optional

from article_factory.database import get_db_session, update_status, get_topic
from article_factory.errors import circuit_breaker, rate_limiter
from article_factory.notebook_lm import NotebookLMClientWrapper
from article_factory.models import TopicStatus

logger = logging.getLogger(__name__)

DISALLOWED_PATTERNS = [
    r"\b(hack|exploit|vulnerability|attack)\b.*\b(software|system|server|network)\b",
    r"\b(steal|stealing|stolen)\b.*\b(data|credentials|passwords|keys)\b",
    r"\b(child|minor).*(abuse|exploitation|nudity|sexual)\b",
    r"\b(generate|create|write).*(malware|virus|ransomware|trojan)\b",
]

def apply_safety_constraints(prompt: str) -> str:
    """Apply safety constraints to user prompt."""
    constrained_prompt = prompt
    for pattern in DISALLOWED_PATTERNS:
        if re.search(pattern, prompt, re.IGNORECASE):
            logger.warning(f"Safety constraint triggered by pattern: {pattern}")
            raise ValueError(f"Prompt contains disallowed content matching pattern: {pattern}")
    return constrained_prompt

def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())

def validate_article_length(article: str, min_words: int = 2000, max_words: int = 2500) -> bool:
    """Validate article is within word count range."""
    word_count = count_words(article)
    if word_count < min_words:
        logger.warning(f"Article too short: {word_count} words (min: {min_words})")
        return False
    if word_count > max_words:
        logger.warning(f"Article too long: {word_count} words (max: {max_words})")
        return False
    return True

def extract_sources_from_article(article: str) -> list:
    """Extract source citations from article."""
    source_pattern = r"\[source:([^\]]+)\]"
    matches = re.findall(source_pattern, article)
    return matches

def enforce_source_citations(article: str, available_sources: list) -> str:
    """Verify article only cites sources from notebook."""
    cited_sources = extract_sources_from_article(article)
    available_source_ids = [s.get("id") or s.get("url") for s in available_sources]
    invalid_sources = [s for s in cited_sources if s not in available_source_ids]
    if invalid_sources:
        logger.warning(f"Invalid citations detected: {invalid_sources}")
        raise ValueError(f"Article cites sources not in notebook: {invalid_sources}")
    return article

async def get_notebook_sources(notebook_id: str) -> list:
    """Get sources from notebook for citation enforcement."""
    client = NotebookLMClientWrapper()
    try:
        async with await client.get_client() as api_client:
            notebook = await api_client.notebooks.get(notebook_id)
            sources = []
            if hasattr(notebook, 'sources'):
                for source in notebook.sources:
                    sources.append({
                        "id": source.id,
                        "url": source.url if hasattr(source, 'url') else None,
                        "title": source.title if hasattr(source, 'title') else None,
                    })
            return sources
    except Exception as e:
        logger.error(f"Failed to get notebook sources: {e}")
        return []

async def generate_article(
    topic_id: int,
    prompt: str,
    prompt_file: Optional[str] = None,
    min_words: int = 2000,
    max_words: int = 2500,
) -> str:
    """Generate article for a topic using NotebookLM API with dynamic prompting.
    
    Args:
        topic_id: Database ID of the topic
        prompt: Inline article generation prompt
        prompt_file: Optional path to file containing prompt
        min_words: Minimum word count for article
        max_words: Maximum word count for article
        
    Returns:
        Generated article text
        
    Raises:
        ValueError: If prompt is invalid or contains disallowed content
        RuntimeError: If article generation fails
    """
    # Resolve prompt from file if provided
    resolved_prompt = prompt
    if prompt_file:
        if not os.path.exists(prompt_file):
            raise ValueError(f"Prompt file not found: {prompt_file}")
        with open(prompt_file, 'r') as f:
            resolved_prompt = f.read()
    
    # Apply safety constraints
    resolved_prompt = apply_safety_constraints(resolved_prompt)
    
    # Load topic to get notebook_id
    topic = get_topic(topic_id)
    if topic is None:
        raise ValueError(f"Topic {topic_id} not found")
    
    notebook_id = topic.get("notebook_id") if isinstance(topic, dict) else topic.notebook_id
    if not notebook_id:
        raise ValueError(f"Topic {topic_id} has no notebook_id - run research first")
    
    # Update status to PROCESSING
    async with get_session() as session:
        await update_status(session, topic_id, TopicStatus.PROCESSING)
    
    # Get notebook sources for citation enforcement
    sources = await get_notebook_sources(notebook_id)
    
    # Build the full prompt with context
    full_prompt = f"""{resolved_prompt}

Based on the notebook sources, write a comprehensive article that:
1. Is {min_words}-{max_words} words
2. Cites sources using [source:id] format for each citation
3. Uses only sources from the notebook
4. Is well-structured with sections and transitions
"""
    
    # Execute article generation with rate limiting and circuit breaker
    client = NotebookLMClientWrapper()
    
    try:
        async with rate_limiter.acquire():
            async with circuit_breaker.call:
                async with await client.get_client() as api_client:
                    result = await api_client.artifacts.generate(
                        notebook_id=notebook_id,
                        instructions=full_prompt,
                    )
                    task_id = result.task_id if hasattr(result, 'task_id') else result.get('task_id')
                    
                    # Wait for completion
                    completion = await client.wait_for_completion(notebook_id, task_id)
                    
                    # Get the generated article
                    article_content = await get_artifact_content(api_client, notebook_id, task_id)
                    
    except Exception as e:
        logger.error(f"Article generation failed for topic {topic_id}: {e}")
        async with get_session() as session:
            await update_status(session, topic_id, TopicStatus.FAILED)
        raise RuntimeError(f"Article generation failed: {e}")
    
    # Enforce source-only citations
    try:
        article_content = enforce_source_citations(article_content, sources)
    except ValueError as e:
        logger.error(f"Citation enforcement failed: {e}")
        async with get_session() as session:
            await update_status(session, topic_id, TopicStatus.FAILED)
        raise
    
    # Validate length
    if not validate_article_length(article_content, min_words, max_words):
        async with get_session() as session:
            await update_status(session, topic_id, TopicStatus.FAILED)
        raise ValueError("Generated article does not meet length requirements")
    
    # Update status to COMPLETED
    async with get_session() as session:
        await update_status(session, topic_id, TopicStatus.COMPLETED)
    
    logger.info(f"Article generated successfully for topic {topic_id}: {count_words(article_content)} words")
    
    return article_content

async def get_artifact_content(api_client, notebook_id: str, artifact_id: str) -> str:
    """Get the content of a generated artifact."""
    try:
        artifact = await api_client.artifacts.get(notebook_id, artifact_id)
        if hasattr(artifact, 'content'):
            return artifact.content
        elif hasattr(artifact, 'text'):
            return artifact.text
        else:
            return str(artifact)
    except Exception as e:
        logger.error(f"Failed to get artifact content: {e}")
        return ""

def save_article(topic_id: int, article_text: str, output_dir: str) -> str:
    """Save article to file.
    
    Args:
        topic_id: Topic database ID
        article_text: Article content
        output_dir: Output directory path
        
    Returns:
        Path to saved article file
    """
    topic = get_topic(topic_id)
    topic_name = topic.get("topic") if isinstance(topic, dict) else topic.topic
    date = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(topic_name)
    filename = f"{date}__{slug}/article.md"
    
    filepath = os.path.join(output_dir, filename) if output_dir else filename
    
    os.makedirs(os.path.dirname(filepath) if output_dir else ".", exist_ok=True)
    
    with open(filepath, 'w') as f:
        f.write(article_text)
    
    logger.info(f"Article saved: {filepath}")
    return filepath

def slugify(text: str) -> str:
    """Convert topic to URL-safe slug."""
    import slugify as _slugify
    return _slugify(text, max_length=80)
