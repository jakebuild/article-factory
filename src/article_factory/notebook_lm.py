"""NotebookLM API client wrapper for async operations."""
import os
import json
from pathlib import Path
from typing import Optional
from notebooklm import NotebookLMClient

ARTICLE_FACTORY_AUTH_PATH = Path.home() / ".article-factory" / "storage_state.json"


class NotebookLMClientWrapper:
    """Wrapper around notebooklm-py NotebookLMClient."""

    def __init__(self):
        auth_json = os.environ.get("NOTEBOOKLM_AUTH_JSON")
        if auth_json:
            self._auth_path = "/tmp/nblm_auth.json"
            with open(self._auth_path, "w") as f:
                f.write(auth_json)
        elif ARTICLE_FACTORY_AUTH_PATH.exists():
            self._auth_path = str(ARTICLE_FACTORY_AUTH_PATH)
        else:
            self._auth_path = None

    async def get_client(self) -> NotebookLMClient:
        """Get authenticated NotebookLM client."""
        if not self._auth_path and not os.environ.get("NOTEBOOKLM_AUTH_JSON"):
            raise ValueError(
                "NotebookLM authentication not configured. "
                "Run 'article-factory login' or set NOTEBOOKLM_AUTH_JSON"
            )

        path = self._auth_path if self._auth_path else None
        client = await NotebookLMClient.from_storage(path)
        return client
    
    async def create_notebook(self, name: str) -> str:
        """Create a new notebook, return notebook_id."""
        async with await self.get_client() as client:
            nb = await client.notebooks.create(name)
            return nb.id
    
    async def get_notebook(self, notebook_id: str) -> dict:
        """Get notebook details."""
        async with await self.get_client() as client:
            nb = await client.notebooks.get(notebook_id)
            return {"id": nb.id, "title": nb.title}
    
    async def start_research(self, notebook_id: str, query: str) -> dict:
        """Start deep research on notebook, return task_id."""
        async with await self.get_client() as client:
            result = await client.research.start(
                notebook_id,
                query=query,
                source="web",
                mode="deep"
            )
            return {"task_id": result["task_id"]}
    
    async def poll_research(self, notebook_id: str) -> dict:
        """Poll research status, return completed sources."""
        async with await self.get_client() as client:
            status = await client.research.poll(notebook_id)
            return status
    
    async def generate_audio(self, notebook_id: str, instructions: str = "") -> dict:
        """Generate audio overview, return task_id."""
        async with await self.get_client() as client:
            status = await client.artifacts.generate_audio(
                notebook_id,
                instructions=instructions
            )
            return {"task_id": status.task_id}
    
    async def wait_for_completion(self, notebook_id: str, task_id: str, timeout: int = 2700) -> dict:
        """Wait for artifact completion."""
        async with await self.get_client() as client:
            status = await client.artifacts.wait_for_completion(
                notebook_id, task_id, timeout=timeout
            )
            return {"status": status.status, "url": status.url}
    
    async def download_audio(self, notebook_id: str, output_path: str, artifact_id: str = None) -> str:
        """Download audio to file."""
        async with await self.get_client() as client:
            path = await client.artifacts.download_audio(
                notebook_id, output_path, artifact_id
            )
            return path

    async def import_sources(self, notebook_id: str, task_id: str, sources: list) -> list:
        """Import research sources into notebook."""
        async with await self.get_client() as client:
            imported = await client.research.import_sources(notebook_id, task_id, sources)
            return imported
