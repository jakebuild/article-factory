---
phase: 01-foundation
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified:
  - "pyproject.toml"
  - "src/article_factory/__init__.py"
  - "src/article_factory/models.py"
  - "src/article_factory/database.py"
autonomous: true
user_setup: []
---

<objective>
Establish project foundation with Poetry, SQLAlchemy models, and SQLite database schema for topic persistence.

Purpose: Creates the infrastructure foundation that all subsequent plans depend on. Enables pip installation and crash recovery capabilities.

Output:
- Poetry project with pyproject.toml
- SQLAlchemy models for Topic entity with state machine
- SQLite database with WAL mode for concurrent access
- Package structure ready for CLI commands
</objective>

<execution_context>
@/Users/giangnguyen/.config/opencode/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
# Phase 1 Goal
User can install CLI and manage topic lifecycle with persistent state

# Key Technical Decisions (Locked)
- Poetry for dependency management
- SQLAlchemy 2.0 with SQLite (sync for Phase 1 simplicity)
- State machine: NEW → PENDING → PROCESSING → COMPLETED → FAILED
- Idempotent operations via retry_count tracking
- Max 3 concurrent topics (enforced later)
</context>

<tasks>

<task type="auto">
  <name>Create Poetry project structure with pyproject.toml</name>
  <files>pyproject.toml, src/article_factory/__init__.py</files>
  <action>
    Create pyproject.toml with:
    - name = "article-factory"
    - version = "0.1.0"
    - description = "A programmable research-backed publishing engine"
    - dependencies: typer>=0.12.0, sqlalchemy>=2.0.0, aiosqlite>=0.19.0, pydantic>=2.0.0
    - [tool.poetry.scripts] entrypoint: article-factory = "article_factory.main:app"
    - [build-system] requires = ["poetry-core"]

    Create src/article_factory/__init__.py with:
    - __version__ = "0.1.0"
    - Export main app for CLI entry point
  </action>
  <verify>
    Run `ls -la pyproject.toml src/article_factory/` and verify both files exist
    Run `poetry install` (if Poetry available) or verify pyproject.toml structure
  </verify>
  <done>
    Project structure exists with pyproject.toml ready for pip install
  </done>
</task>

<task type="auto">
  <name>Define SQLAlchemy Topic model with state machine</name>
  <files>src/article_factory/models.py</files>
  <action>
    Create Topic model with:
    - id: Integer primary key (auto-increment)
    - topic: String (required, user-provided topic name)
    - prompt: String (required, user-provided writing prompt)
    - status: Enum(NEW, PENDING, PROCESSING, COMPLETED, FAILED) default NEW
    - notebook_id: String, nullable (NotebookLM notebook ID)
    - artifact_ids: JSON (list of artifact IDs from NotebookLM)
    - retry_count: Integer default 0
    - created_at: DateTime default now
    - updated_at: DateTime default now, onupdate now

    Define state machine transitions:
    - NEW → PENDING (when enqueued for processing)
    - PENDING → PROCESSING (when work starts)
    - PROCESSING → COMPLETED (on success)
    - PROCESSING → FAILED (on error, increments retry_count)
    - FAILED → PENDING (on retry, increments retry_count)
  </action>
  <verify>
    Run `python -c "from article_factory.models import Topic; print(Topic.__tablename__)"` and verify no errors
  </verify>
  <done>
    Topic model defines all required fields and state transitions
  </done>
</task>

<task type="auto">
  <name>Implement SQLite database with crash recovery support</name>
  <files>src/article_factory/database.py</files>
  <action>
    Create database module with:
    - SQLite URL: sqlite:///article_factory.db (in project root or XDG data dir)
    - Engine with WAL mode enabled for concurrent async access
    - SessionLocal: scoped session for request/transaction
    - Base: declarative base from SQLAlchemy

    Implement idempotent operations:
    - create_topic(topic, prompt) → Topic: Creates new topic, handles duplicate topic+prompt gracefully
    - get_topic(id) → Topic: Retrieves topic by ID
    - get_all_topics() → List[Topic]: Returns all topics ordered by created_at desc
    - update_status(id, new_status) → Topic: Updates status with transition validation
    - increment_retry(id) → Topic: Increments retry_count atomically
    - set_notebook_id(id, notebook_id) → Topic: Sets notebook_id for tracking
    - add_artifact(id, artifact_id) → Topic: Appends artifact_id to artifact_ids list
    - get_pending_topics() → List[Topic]: Returns topics ready for processing

    Implement crash recovery helper:
    - recover_crashed_topics(): Sets PROCESSING topics back to PENDING (orphaned work)
  </action>
  <verify>
    Run `python -c "from article_factory.database import engine, SessionLocal; print('Database module loads successfully')"`
    Verify `article_factory.db` is created when importing
  </verify>
  <done>
    Database module provides all CRUD operations with crash recovery support
  </done>
</task>

</tasks>

<verification>
1. Verify pyproject.toml is valid TOML and has correct structure
2. Verify Topic model has all required fields: id, topic, prompt, status, notebook_id, artifact_ids, retry_count, created_at, updated_at
3. Verify database module creates article_factory.db on import
4. Verify all database operations work without errors
5. Verify crash recovery sets PROCESSING topics to PENDING
</verification>

<success_criteria>
- User can run `pip install -e .` and access `article-factory` command
- Topic metadata persists in SQLite database
- Crash recovery is functional (PROCESSING → PENDING)
- retry_count is tracked per topic
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation/01-setup-SUMMARY.md`
</output>
