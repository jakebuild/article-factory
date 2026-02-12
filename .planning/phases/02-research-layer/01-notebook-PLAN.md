---
phase: 02-research-layer
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified:
  - "src/article_factory/notebook_lm.py"
  - "src/article_factory/notebooks.py"
autonomous: true
user_setup:
  - service: notebooklm
  - why: "NotebookLM API authentication"
  - env_vars:
    - name: NOTEBOOKLM_API_KEY
      source: "NotebookLM settings or API credentials"
  - dashboard_config:
    - task: "Obtain API credentials"
      location: "https://notebooklm.google.com/"
---

<objective>
Integrate NotebookLM client SDK and implement notebook CRUD operations.

Purpose: Enables the system to create notebooks, trigger deep research, and persist notebooks for knowledge compounding. Builds on Phase 1's state management.

Output:
- NotebookLM client wrapper with async support
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

# Phase 1 Dependencies
- Uses Topic model from src/article_factory/models.py
- Uses database operations from src/article_factory/database.py
- Status transitions: PENDING → PROCESSING → COMPLETED/FAILED

# Key Technical Decisions
- Use notebooklm-py SDK for NotebookLM API integration
- Notebook names use format: YYYY-MM-DD__topic-slug
- Notebooks are never deleted (permanent persistence)
- WAL mode required for concurrent async operations
</context>

<tasks>

<task type="auto">
  <name>Create NotebookLM client wrapper</name>
  <files>src/article_factory/notebook_lm.py</files>
  <action>
    Create notebook_lm.py with:
    - NotebookLMClient initialization from environment variable NOTEBOOKLM_API_KEY
    - Async context manager support for the client
    - Methods:
      - create_notebook(name) → notebook_id
      - get_notebook(notebook_id) → notebook details
      - add_source(notebook_id, source_content) → source_id
      - add_research(notebook_id, query, mode="deep") → artifact_id
      - wait_for_artifact(artifact_id, timeout=2700) → artifact result
      - generate_text(notebook_id, prompt) → text artifact
      - generate_image(notebook_id, prompt) → image artifact
      - generate_audio(notebook_id, prompt) → audio artifact

    Error handling:
    - ValueError for missing API key
    - TimeoutError for artifact polling timeout
    - RuntimeError for API errors
  </action>
  <verify>
    Run `python -c "from article_factory.notebook_lm import NotebookLMClient; print('NotebookLM client module loads')" 2>&1`
    Verify environment variable check works: "NOTEBOOKLM_API_KEY not set" error
  </verify>
  <done>
    NotebookLM client wrapper provides all methods needed for research workflow
  </done>
</task>

<task type="auto">
  <name>Implement notebook operations module</name>
  <files>src/article_factory/notebooks.py</files>
  <action>
    Create notebooks.py with:

    Notebook naming:
    - slugify(topic: str) → YYYY-MM-DD__topic-slug-format
    - create_notebook_name(topic: str) → full notebook name

    Notebook CRUD:
    - create_notebook(topic: str) → (notebook_id, name): Creates notebook, updates topic in DB
    - get_notebook(notebook_id: str) → dict: Fetches notebook details
    - add_source_to_notebook(notebook_id: str, content: str) → source_id
    - trigger_deep_research(notebook_id: str, query: str) → artifact_id

    State integration:
    - Uses database.py operations to update topic with notebook_id
    - Sets status to PROCESSING when research starts
    - Validates topic exists before operations
  </action>
  <verify>
    Run `python -c "from article_factory.notebooks import create_notebook_name, slugify; print('Notebook operations module loads')" 2>&1`
    Test slugify: slugify("Bitcoin ETF") should return "2026-02-12__bitcoin-etf"
  </verify>
  <done>
    Notebook operations module integrates with Phase 1 database and provides notebook CRUD
  </done>
</task>

<task type="auto">
  <name>Enable WAL mode for concurrent async access</name>
  <files>src/article_factory/database.py</files>
  <action>
    Update database.py to:
    - Enable WAL mode on SQLite connection: `PRAGMA journal_mode=WAL`
    - Set synchronous=NORMAL for better performance with WAL
    - Connection pooling: create_engine with pool_size=5, max_overflow=10
    - Verify WAL mode on startup: print("Database initialized with WAL mode")

    Update SessionLocal to use async session maker:
    - from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    - Use aiosqlite for async SQLite access
  </action>
  <verify>
    Run `python -c "from article_factory.database import engine; print('Database with WAL mode loads')" 2>&1`
    Check for "WAL mode" in initialization output
  </verify>
  <done>
    Database configured with WAL mode for concurrent async access (STATE-05 complete)
  </done>
</task>

</tasks>

<verification>
1. Verify NotebookLM client wrapper has all required methods
2. Verify notebook name generation uses correct slug format
3. Verify WAL mode is enabled on database connection
4. Verify notebook operations integrate with Phase 1 database
5. Verify environment variable check for API key
</verification>

<success_criteria>
- NotebookLM client ready for API calls
- Notebooks created with format YYYY-MM-DD__topic-slug
- WAL mode enabled for concurrent access
- Integration with Phase 1 state management works
</success_criteria>

<output>
After completion, create `.planning/phases/02-research-layer/01-notebook-SUMMARY.md`
</output>
