# Stack Research

**Domain:** Python CLI Application with NotebookLM Integration
**Researched:** 2026-02-12
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12+ | Core language runtime | Latest async improvements, type system enhancements, optimal performance for CLI applications |
| Typer | 0.12+ | CLI framework with type hints | Modern decorator-based syntax leveraging Python type hints; built on Click for compatibility; auto-generates help documentation; supports async commands natively |
| SQLAlchemy | 2.0.36+ | ORM with async support | Full async ORM capabilities via AsyncSession; first-class SQLite support; mature ecosystem; declarative migration management with Alembic |
| aiosqlite | 0.21+ | Async SQLite driver | Native async interface to sqlite3; context manager support; non-blocking database operations for CLI workflows |
| notebooklm-py | Latest | NotebookLM client integration | Official unofficial Python SDK; async context manager support; complete API coverage for notebooks, sources, and artifacts |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pydantic | 2.10+ | Data validation & settings | Configuration management; type-safe settings via pydantic-settings; CLI argument validation |
| Alembic | 1.14+ | Database migrations | Schema evolution; migration tracking; integrates with SQLAlchemy models |
| Rich | 13.7+ | Terminal output formatting | Progress bars; styled output; tables; syntax highlighting for CLI UX |
| httpx | 0.28+ | Async HTTP client | External API calls; NotebookLM API communication; concurrent request handling |
| structlog | 24.3+ | Structured logging | JSON logs for automation; contextual logging for debugging CLI workflows |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Poetry | Dependency management | Lock files; virtualenv management; publishing support; deterministic builds |
| ruff | Fast linting & formatting | 10-100x faster than flake8/black; single tool for lint + format; minimal configuration |
| pytest | Testing framework | Async test support via pytest-asyncio; fixture patterns; parametrized tests |
| pytest-asyncio | Async test support | Native async test execution; concurrent test runs |
| mypy | Static type checking | Type safety; catch errors early; integrates with IDEs |

## Installation

```bash
# Core dependencies
pip install "typer>=0.12.0" \
           "sqlalchemy>=2.0.0" \
           "aiosqlite>=0.21.0" \
           "notebooklm-py>=0.3.0" \
           "pydantic>=2.10.0" \
           "pydantic-settings>=2.6.0" \
           "rich>=13.7.0" \
           "httpx>=0.28.0"

# Database migrations
pip install "alembic>=1.14.0"

# Logging
pip install "structlog>=24.3.0"

# Development tools
pip install -D "poetry>=1.8.0" \
               "ruff>=0.8.0" \
               "pytest>=8.3.0" \
               "pytest-asyncio>=0.24.0" \
               "mypy>=1.13.0"
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Typer | Click 8.1 | When maximum control over CLI behavior is needed; when avoiding type hint dependencies; for simpler projects |
| Typer | argparse | When no external dependencies allowed; for very simple scripts with basic argument parsing |
| SQLAlchemy 2.0 | raw sqlite3 + SQL | When ORM overhead is unacceptable; for extremely lightweight scripts with simple queries |
| SQLAlchemy 2.0 | SQLModel | When combining FastAPI with CLI; when wanting SQLAlchemy+Pydantic unification |
| Dramatiq (recommended below) | Celery 5.4 | When enterprise features needed; when migrating existing Celery infrastructure; when RabbitMQ is preferred over Redis |
| notebooklm-py | nblm-rs (Rust CLI) | When NotebookLM Enterprise API access; when maximum performance needed; when integrating with Rust tooling |
| aiosqlite | databases ORM | When wanting simpler async ORM; when using Encode framework ecosystem |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Click decorators for complex CLIs | Verbose for large command hierarchies; type safety gaps; manual help generation | Typer (built on Click, adds type hints) |
| SQLAlchemy 1.x | Missing native async patterns; deprecated patterns; slower ORM initialization | SQLAlchemy 2.0+ with async_engine |
| asyncio queues directly | No persistence; no retry logic; manual worker management; no scheduling | Dramatiq or Taskiq |
| Celery for new projects | Complex broker setup; heavy dependencies; steep learning curve; over-engineered for simple CLI use | Dramatiq (simpler API, better defaults) |
| print() for output | No styling; no progress indication; hard to parse; poor UX | Rich library |
| dict-based config | No validation; runtime errors; hard to document; error-prone | Pydantic-settings |
| json module for logging | No structured output; hard to parse; no levels | structlog |

## Task Queue Decision: Dramatiq vs Taskiq vs Celery

For a CLI-based research tool with async job processing, **Dramatiq** is the recommended choice:

| Criterion | Dramatiq | Taskiq | Celery |
|-----------|----------|--------|--------|
| Setup complexity | Low | Low | High |
| Async native | Yes (threading) | Yes (async-first) | Partial (requires eventlet/gevent) |
| Broker options | Redis, RabbitMQ | Redis | Redis, RabbitMQ, SQS |
| Performance | Excellent (4.12s for 20k jobs) | Best (2.03s for 20k jobs) | Good (11.68s threads) |
| CLI ergonomics | Good | Good | Excellent (celery worker) |
| Retry logic | Built-in with backoff | Built-in | Built-in |
| Scheduling | APScheduler integration | Native | Celery Beat |

**Recommendation: Dramatiq** for simplicity and balance of features. **Taskiq** for maximum async performance.

## Stack Patterns by Variant

**If NotebookLM automation focus:**
- Use notebooklm-py as primary integration
- Minimal task queue (in-memory queue or Dramatiq with Redis)
- Focus on async/await patterns for API calls

**If heavy content generation pipeline:**
- Dramatiq with Redis broker for job persistence
- Rich for progress visualization
- Structlog for job audit trails

**If single-user CLI tool:**
- In-memory task queue or threading
- SQLite only (no Redis dependency)
- Typer + Rich for polished UX

**If multi-user/research team:**
- Dramatiq with Redis for shared state
- SQLAlchemy for user/project data
- Full async architecture

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Python 3.12+ | All listed packages | Required for optimal async performance |
| Typer 0.12+ | Click 8.1+ | Typer depends on Click |
| SQLAlchemy 2.0+ | aiosqlite 0.21+ | aiosqlite provides async sqlite3 wrapper |
| SQLAlchemy 2.0+ | Alembic 1.14+ | Full migration support for async engines |
| Pydantic 2.10+ | pydantic-settings 2.6+ | SettingsConfigDict for .env support |
| notebooklm-py | httpx 0.28+ | Uses httpx for async HTTP |
| Dramatiq | redis 5.0+ | Redis broker support |

## Critical Integration Points

### Typer + SQLAlchemy Async

```python
# typer_app.py
import typer
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_async_session

app = typer.Typer()

@app.command()
def create_project(name: str, description: str = None):
    """Create a new research project."""
    async def _create():
        async with get_async_session() as session:
            # Database operations here
            pass
    typer.run(lambda: asyncio.run(_create()))
```

### Dramatiq Actor for Long-Running Research

```python
# tasks.py
import dramatiq
from dramatiq.middleware import Retries

@dramatiq.actor(max_retries=3, min_backoff=1000)
def run_research_task(project_id: str, query: str):
    """Execute research task asynchronously."""
    # Long-running NotebookLM operations
    pass
```

### notebooklm-py Async Context Manager

```python
# notebooklm_client.py
import asyncio
from notebooklm import NotebookLMClient

async def analyze_sources(notebook_id: str):
    async with await NotebookLMClient.from_storage() as client:
        # Async NotebookLM operations
        pass
```

## Sources

- **Typer Documentation** — https://typer.tiangolo.com/ (current as of Feb 2026)
- **SQLAlchemy 2.0 Async Documentation** — https://docs.sqlalchemy.org/en/latest/orm/extensions/asyncio.html (version 2.0.36, Jan 2026)
- **aiosqlite Documentation** — https://aiosqlite.omnilib.dev/en/stable/ (version 0.21.0, 2025)
- **Dramatiq Documentation** — https://dramatiq.readthedocs.io/en/latest/ (version 1.14, 2025)
- **notebooklm-py GitHub** — https://github.com/teng-lin/notebooklm-py (active maintenance, Feb 2026)
- **Python Task Queue Benchmarks** — https://github.com/steventen/python_queue_benchmark (updated Nov 2025)
- **Rich Library** — https://rich.readthedocs.io/en/stable/ (version 13.7, 2025)

---
*Stack research for: NotebookLM Article Factory CLI*
*Researched: 2026-02-12*
