"""Notebook operations for research workflow integration."""
from datetime import datetime
from slugify import slugify as _slugify
from article_factory.database import get_session, update_status, set_notebook_id
from article_factory.notebook_lm import NotebookLMClientWrapper


def slugify(text: str) -> str:
    """Convert topic to URL-safe slug with timestamp prefix."""
    # Format: YYYY-MM-DD__topic-slug
    date = datetime.now().strftime("%Y-%m-%d")
    topic_slug = _slugify(text, max_length=80)
    return f"{date}__{topic_slug}"


async def create_notebook_for_topic(topic_id: int, topic: str, prompt: str) -> str:
    """Create notebook, update topic in DB, return notebook_id."""
    # 1. Generate notebook name
    name = slugify(topic)
    
    # 2. Create notebook via API
    client = NotebookLMClientWrapper()
    notebook_id = await client.create_notebook(name)
    
    # 3. Update topic with notebook_id
    async with get_session() as session:
        await set_notebook_id(session, topic_id, notebook_id)
        await update_status(session, topic_id, "PROCESSING")
    
    return notebook_id


async def trigger_deep_research(topic_id: int, notebook_id: str, query: str) -> str:
    """Trigger deep research, return task_id."""
    client = NotebookLMClientWrapper()
    result = await client.start_research(notebook_id, query)
    return result["task_id"]


async def poll_research_status(notebook_id: str) -> dict:
    """Poll research status."""
    client = NotebookLMClientWrapper()
    return await client.poll_research(notebook_id)


async def wait_for_research_completion(notebook_id: str, task_id: str, timeout: int = 2700) -> dict:
    """Wait for research completion."""
    client = NotebookLMClientWrapper()
    return await client.wait_for_completion(notebook_id, task_id, timeout)
