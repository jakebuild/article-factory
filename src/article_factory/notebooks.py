"""Notebook operations for research workflow integration."""
from datetime import datetime
from slugify import slugify as _slugify
from article_factory.database import update_status, set_notebook_id
from article_factory.models import TopicStatus
from article_factory.notebook_lm import NotebookLMClientWrapper


def slugify(text: str) -> str:
    """Convert topic to URL-safe slug with timestamp prefix."""
    date = datetime.now().strftime("%Y-%m-%d")
    topic_slug = _slugify(text, max_length=80)
    return f"{date}__{topic_slug}"


async def create_notebook_for_topic(topic_id: int, topic: str, prompt: str) -> str:
    """Create notebook, update topic in DB, return notebook_id."""
    name = slugify(topic)
    
    client = NotebookLMClientWrapper()
    notebook_id = await client.create_notebook(name)
    
    set_notebook_id(topic_id, notebook_id)
    update_status(topic_id, TopicStatus.PROCESSING)
    
    return notebook_id


async def trigger_deep_research(topic_id: int, notebook_id: str, query: str) -> str:
    """Trigger deep research, return task_id."""
    client = NotebookLMClientWrapper()
    result = await client.start_research(notebook_id, query)
    return result["task_id"]


async def poll_and_import_sources(notebook_id: str, task_id: str, timeout: int = 600) -> dict:
    """Poll research status and import all discovered sources.
    
    Args:
        notebook_id: The notebook ID
        task_id: The research task ID
        timeout: Maximum seconds to wait (default: 10 min)
        
    Returns:
        Dict with status, sources imported count, and any summary
    """
    import time
    client = NotebookLMClientWrapper()
    start_time = time.time()
    
    while True:
        if time.time() - start_time > timeout:
            print(f"Warning: Research poll timed out after {timeout}s")
            return {
                "status": "timeout",
                "sources_imported": 0,
                "summary": "",
                "sources_found": 0,
                "note": "Research timed out"
            }
        
        result = await client.poll_research(notebook_id)
        
        if result.get("status") == "completed":
            sources = result.get("sources", [])
            
            if sources:
                try:
                    imported = await client.import_sources(notebook_id, task_id, sources)
                    return {
                        "status": "completed",
                        "sources_imported": len(imported),
                        "summary": result.get("summary", ""),
                        "sources_found": len(sources)
                    }
                except Exception as e:
                    print(f"Warning: Could not import sources (may require newer notebooklm-py): {e}")
                    return {
                        "status": "completed",
                        "sources_imported": 0,
                        "summary": result.get("summary", ""),
                        "sources_found": len(sources),
                        "note": "Research completed but import failed - notebooklm-py may need update"
                    }
            else:
                return {
                    "status": "completed",
                    "sources_imported": 0,
                    "summary": result.get("summary", ""),
                    "sources_found": 0
                }
        
        elif result.get("status") == "in_progress":
            import asyncio
            await asyncio.sleep(30)
            continue
        
        else:
            return {
                "status": "failed",
                "sources_imported": 0,
                "error": "Research failed or no research found"
            }


async def poll_research_status(notebook_id: str) -> dict:
    """Poll research status."""
    client = NotebookLMClientWrapper()
    return await client.poll_research(notebook_id)


async def wait_for_research_completion(notebook_id: str, task_id: str, timeout: int = 2700) -> dict:
    """Wait for research completion (legacy wrapper, prefer poll_and_import_sources)."""
    return await poll_and_import_sources(notebook_id, task_id, timeout=timeout)
