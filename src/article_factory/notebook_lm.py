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
            return {"status": status.status, "url": status.url, "error": status.error}
    
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

    async def list_sources(self, notebook_id: str) -> list:
        """List all sources in a notebook."""
        async with await self.get_client() as client:
            sources = await client.sources.list(notebook_id)
            return sources

    async def generate_infographic(self, notebook_id: str, instructions: str = None) -> dict:
        """Trigger infographic generation and wait until it reaches COMPLETED status.

        The CREATE_VIDEO RPC returns None even on success, so we track the artifact
        via before/after list diff and poll _list_raw directly (ArtifactStatus.COMPLETED=3)
        rather than using poll_status whose fallback incorrectly maps status=4 to "completed".
        """
        import asyncio as _asyncio
        from notebooklm._artifacts import ArtifactStatus

        # ArtifactTypeCode.INFOGRAPHIC = 7 across all SDK versions
        INFOGRAPHIC = 7

        async with await self.get_client() as client:
            # Delete all previously failed infographic artifacts to avoid
            # hitting NotebookLM rate limits from stale failed attempts
            raw_before = await client.artifacts._list_raw(notebook_id)
            failed_ids = [
                a[0] for a in raw_before
                if isinstance(a, list) and len(a) > 4
                and a[2] == INFOGRAPHIC
                and a[4] == ArtifactStatus.FAILED
            ]
            for artifact_id in failed_ids:
                try:
                    await client.artifacts.delete(notebook_id, artifact_id)
                except Exception:
                    pass

            # Snapshot existing completed infographic IDs
            completed_before = {
                a[0] for a in raw_before
                if isinstance(a, list) and len(a) > 4
                and a[2] == INFOGRAPHIC
                and a[4] == ArtifactStatus.COMPLETED
            }

            # Trigger generation — orientation=LANDSCAPE + detail=STANDARD required for success
            from notebooklm._artifacts import InfographicOrientation, InfographicDetail
            await client.artifacts.generate_infographic(
                notebook_id,
                instructions=instructions,
                orientation=InfographicOrientation.LANDSCAPE,
                detail_level=InfographicDetail.STANDARD,
            )
            await _asyncio.sleep(3)

            # Find the new artifact via diff
            raw_after = await client.artifacts._list_raw(notebook_id)
            new_arts = [
                a for a in raw_after
                if isinstance(a, list) and len(a) > 4
                and a[2] == INFOGRAPHIC
                and a[0] not in completed_before
            ]
            if not new_arts:
                raise RuntimeError("Infographic trigger sent but no new artifact appeared")

            new_id = new_arts[0][0]

            # Poll until COMPLETED or FAILED
            timeout, interval, elapsed = 300, 5, 0
            while elapsed < timeout:
                await _asyncio.sleep(interval)
                elapsed += interval
                raw = await client.artifacts._list_raw(notebook_id)
                art = next((a for a in raw if isinstance(a, list) and len(a) > 0 and a[0] == new_id), None)
                if art is None:
                    raise RuntimeError(f"Infographic artifact {new_id} disappeared")
                status_code = art[4] if len(art) > 4 else None
                if status_code == ArtifactStatus.COMPLETED:
                    return {"task_id": new_id}
                if status_code == ArtifactStatus.FAILED:
                    raise RuntimeError("NotebookLM infographic generation failed (FAILED status)")

            raise RuntimeError(f"Infographic generation timed out after {timeout}s")

    async def download_infographic(self, notebook_id: str, output_path: str) -> str:
        """Download infographic PNG to file."""
        async with await self.get_client() as client:
            path = await client.artifacts.download_infographic(notebook_id, output_path)
            return path
