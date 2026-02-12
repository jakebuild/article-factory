"""Research orchestration for NotebookLM deep research operations.

Provides async workflow for:
- Triggering research on topics
- Polling for completion
- Generating synthesis from results
"""
import asyncio
import os
from datetime import datetime
from typing import Optional

from article_factory.notebook_lm import NotebookLMClientWrapper
from article_factory.errors import RateLimiter, CircuitBreaker, CircuitOpenError
from article_factory.database import (
    get_topic, update_status, increment_retry, set_notebook_id
)

# Global rate limiter and circuit breaker for research operations
rate_limiter = RateLimiter(max_concurrent=3, min_interval=120)
circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=300)


async def start_research(topic_id: int):
    """Start research for a topic.
    
    Creates a notebook, triggers deep research, and updates status.
    
    Args:
        topic_id: Database ID of the topic to research
        
    Returns:
        Dict with notebook_id and status
        
    Raises:
        ValueError: If topic is not in PENDING status
        CircuitOpenError: If circuit breaker is open
    """
    # Get topic from database
    topic_data = get_topic(topic_id)
    if not topic_data:
        raise ValueError(f"Topic {topic_id} not found")
    
    topic_status = topic_data.get('status')
    if topic_status != 'PENDING':
        raise ValueError(f"Topic {topic_id} is {topic_status}, expected PENDING")
    
    topic_name = topic_data.get('topic')
    topic_prompt = topic_data.get('prompt', '')
    
    client = NotebookLMClientWrapper()
    
    # Create notebook for this topic
    await rate_limiter.acquire()
    try:
        notebook_id = await client.create_notebook(topic_name)
    finally:
        rate_limiter.release()
    
    # Save notebook_id to database
    set_notebook_id(topic_id, notebook_id)
    
    # Trigger research
    await rate_limiter.acquire()
    try:
        await circuit_breaker.call(
            client.start_research, notebook_id, topic_prompt or topic_name
        )
    except CircuitOpenError:
        # Research trigger failed but notebook was created
        raise
    finally:
        rate_limiter.release()
    
    # Update status to PROCESSING
    update_status(topic_id, 'PROCESSING')
    
    return {"notebook_id": notebook_id, "status": "PROCESSING"}


async def poll_research(topic_id: int, poll_interval: int = 60, timeout: int = 2700):
    """Poll research completion status.
    
    Args:
        topic_id: Database ID of the topic
        poll_interval: Seconds between status checks (default: 60)
        timeout: Maximum seconds to wait (default: 45 min)
        
    Returns:
        Dict with status and sources on completion
        
    Raises:
        TimeoutError: If research doesn't complete within timeout
        CircuitOpenError: If circuit breaker is open
    """
    topic_data = get_topic(topic_id)
    if not topic_data:
        raise ValueError(f"Topic {topic_id} not found")
    
    notebook_id = topic_data.get('notebook_id')
    if not notebook_id:
        raise ValueError(f"Topic {topic_id} has no notebook_id")
    
    client = NotebookLMClientWrapper()
    start_time = asyncio.get_event_loop().time()
    
    while True:
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed > timeout:
            raise TimeoutError(f"Research timed out after {timeout}s")
        
        # Check research status
        await rate_limiter.acquire()
        try:
            status = await circuit_breaker.call(
                client.poll_research, notebook_id
            )
        except CircuitOpenError:
            raise
        finally:
            rate_limiter.release()
        
        # Handle status
        if status.get('status') == 'completed':
            sources = status.get('sources', [])
            update_status(topic_id, 'COMPLETED')
            return {"status": "completed", "sources": sources}
        
        elif status.get('status') == 'in_progress':
            # Wait and poll again
            await asyncio.sleep(poll_interval)
            continue
        
        else:
            # Failed or unknown status
            update_status(topic_id, 'FAILED')
            increment_retry(topic_id)
            raise RuntimeError(f"Research failed with status: {status.get('status')}")


async def run_research(topic_id: int):
    """Blocking call: start research and wait for completion.
    
    This is a convenience function that chains start_research and poll_research.
    
    Args:
        topic_id: Database ID of the topic
        
    Returns:
        Result from poll_research
        
    Raises:
        Exception: Any error from the research workflow
    """
    try:
        # Start the research
        result = await start_research(topic_id)
        
        # Poll for completion
        result = await poll_research(topic_id)
        
        return result
        
    except Exception as e:
        # Ensure status is updated on failure
        try:
            update_status(topic_id, 'FAILED')
            increment_retry(topic_id)
        except Exception:
            pass  # Don't mask original error
        raise


async def generate_synthesis(notebook_id: str, topic_slug: str) -> str:
    """Generate research synthesis and save to file.
    
    Uses the NotebookLM chat API to create a structured summary
    of research sources and key insights.
    
    Args:
        notebook_id: NotebookLM notebook ID
        topic_slug: URL-safe topic identifier for output path
        
    Returns:
        Path to the generated synthesis file
    """
    client = NotebookLMClientWrapper()
    
    # Generate synthesis via chat API
    await rate_limiter.acquire()
    try:
        result = await circuit_breaker.call(
            client.chat.ask, notebook_id,
            """Create a structured summary of all sources and key insights. Format as:

## Key Findings
- [bullet points of main discoveries]

## Sources Summary  
- [list of sources with brief descriptions]

## Questions Answered
- [Q: question] [A: answer]

## Knowledge Gaps
- [areas that need further research]"""
        )
    except CircuitOpenError:
        raise
    finally:
        rate_limiter.release()
    
    # Save to output directory
    output_dir = f"output/{datetime.now().strftime('%Y-%m-%d')}/{topic_slug}"
    os.makedirs(output_dir, exist_ok=True)
    
    synthesis_path = f"{output_dir}/research_synthesis.md"
    with open(synthesis_path, "w") as f:
        f.write("# Research Synthesis\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Notebook ID: {notebook_id}\n\n")
        f.write("---\n\n")
        if hasattr(result, 'answer'):
            f.write(result.answer)
        else:
            f.write(str(result))
    
    return synthesis_path
