---
phase: 02-research-layer
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified:
  - "src/article_factory/notebook_lm.py"
  - "src/article_factory/notebooks.py"
  - "pyproject.toml"
autonomous: true
user_setup:
  - service: notebooklm
  - why: "NotebookLM API authentication"
  - env_vars:
    - name: NOTEBOOKLM_AUTH_JSON
      source: "Run `notebooklm login` to authenticate, then extract cookies from ~/.notebooklm/storage_state.json"
  - dashboard_config:
    - task: "Authenticate with NotebookLM"
      location: "Run `pip install notebooklm-py` then `notebooklm login`"
---

<objective>
Integrate notebooklm-py SDK and implement notebook CRUD operations.

Purpose: Enables the system to create notebooks, trigger deep research, and persist notebooks for knowledge compounding using the official notebooklm-py library.

Output:
- notebooklm-py SDK integration with async client
- Notebook creation with timestamped slug format (YYYY-MM-DD__topic-slug)
- Notebook persistence (preserves notebooks permanently)
- WAL mode enabled for concurrent async access
</objective>

<execution_context>
@/Users/giangnguyen/.config/opencode/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
# Phase 2 Goal
System creates notebooks, runs async research, and handles core API errors

# Key Technical Decision (LOCKED)
Use notebooklm-py library from https://github.com/teng-lin/notebooklm-py
- Install: `pip install notebooklm-py`
- Auth: `notebooklm login` or NOTEBOOKLM_AUTH_JSON env var
- Client: NotebookLMClient.from_storage()

# Phase 1 Dependencies
- Uses Topic model from src/article_factory/models.py
- Uses database operations from src/article_factory/database.py
- Status transitions: PENDING → PROCESSING → COMPLETED/FAILED

# Notebook Naming
- Format: YYYY-MM-DD__topic-slug
- Slugify: lowercase, hyphens, max 100 chars
</context>

<tasks>

<task type="auto">
  <name>Add notebooklm-py to dependencies</name>
  <files>pyproject.toml</files>
  <action>
    Update pyproject.toml to add:
    - "notebooklm-py>=0.3.0" from pypi
    
    Keep existing dependencies: typer, sqlalchemy, aiosqlite, pydantic
  </action>
  <verify>
    Run `poetry add notebooklm-py` or verify pyproject.toml contains "notebooklm-py"
  </verify>
  <done>
    notebooklm-py available as project dependency
  </done>
</task>

<task type="auto">
  <name>Create NotebookLM client wrapper</name>
  <files>src/article_factory/notebook_lm.py</files>
  <action>
    Create notebook_lm.py with:

    ```python
    import os
    import json
    from notebooklm import NotebookLMClient

    class NotebookLMClientWrapper:
        """Wrapper around notebooklm-py NotebookLMClient."""
        
        def __init__(self):
            # Load auth from env var or storage
            auth_json = os.environ.get("NOTEBOOKLM_AUTH_JSON")
            if auth_json:
                # Write temp file for from_storage() to read
                self._auth_path = "/tmp/nblm_auth.json"
                with open(self._auth_path, "w") as f:
                    f.write(auth_json)
            else:
                self._auth_path = None
        
        async def get_client(self):
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
    ```

    Error handling:
    - ValueError if auth not configured
    - RuntimeError if API call fails
    - TimeoutError if polling exceeds timeout
  </action>
  <verify>
    Run `python -c "from article_factory.notebook_lm import NotebookLMClientWrapper; print('Wrapper module loads')"`
    Verify auth check: "NOTEBOOKLM_AUTH_JSON not set" error
  </verify>
  <done>
    NotebookLMClientWrapper provides all methods for research workflow
  </done>
</task>

<task type="auto">
  <name>Implement notebook operations module</name>
  <files>src/article_factory/notebooks.py</files>
  <action>
    Create notebooks.py with:

    ```python
    from datetime import datetime
    from slugify import slugify as _slugify
    from article_factory.database import get_session, update_status, set_notebook_id
    from article_factory.notebook_lm import NotebookLMClientWrapper

    def slugify(text: str) -> str:
        """Convert topic to URL-safe slug."""
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
        await set_notebook_id(topic_id, notebook_id)
        await update_status(topic_id, "PROCESSING")
        
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
    ```

    Integration with Phase 1 database:
    - Uses get_session(), update_status(), set_notebook_id()
    - Status transitions: PENDING → PROCESSING → COMPLETED
  </action>
  <verify>
    Run `python -c "from article_factory.notebooks import slugify, create_notebook_for_topic; print('Notebook operations module loads')"`
    Test slugify: slugify("Bitcoin ETF") → "2026-02-12__bitcoin-etf"
  </verify>
  <done>
    Notebook operations module integrates with Phase 1 database
  </done>
</task>

<task type="auto">
  <name>Enable WAL mode for concurrent async access</name>
  <files>src/article_factory/database.py</files>
  <action>
    Update database.py to enable WAL mode:
    
    ```python
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker

    # Enable WAL mode for SQLite
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()
    
    # Async engine for concurrent access
    async_engine = create_async_engine(
        "sqlite+aiosqlite:///article_factory.db",
        pool_size=5,
        max_overflow=10
    )
    AsyncSessionLocal = async_sessionmaker(async_engine)
    ```

    Keep sync engine for backward compatibility, add async for notebooklm-py.
  </action>
  <verify>
    Run `python -c "from article_factory.database import engine, async_engine; print('Database with WAL mode loads')"`
    Verify "PRAGMA journal_mode=WAL" output
  </verify>
  <done>
    Database configured with WAL mode for concurrent async access (STATE-05)
  </done>
</task>

</tasks>

<verification>
1. Verify notebooklm-py added to dependencies
2. Verify NotebookLMClientWrapper has all required methods
3. Verify notebook name generation uses correct slug format
4. Verify WAL mode is enabled on database connection
5. Verify notebook operations integrate with Phase 1 database
</verification>

<success_criteria>
- notebooklm-py SDK integrated and authenticated
- Notebooks created with format YYYY-MM-DD__topic-slug
- WAL mode enabled for concurrent access
- Integration with Phase 1 state management works
</success_criteria>

<output>
After completion, create `.planning/phases/02-research-layer/01-notebook-SUMMARY.md`
</output>
