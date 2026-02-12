# NotebookLM Article Factory

A **programmable research-backed publishing engine** powered entirely by NotebookLM APIs. It separates stable research from fully programmable writing, enabling dynamic prompt injection at runtime.

## What It Does

1. **Authenticates** with NotebookLM via browser login
2. **Creates notebooks** on NotebookLM from your topics
3. **Runs deep research** automatically on each topic
4. **Generates content** using your custom prompts:
   - Research synthesis from discovered sources
   - Long-form articles (from synthesis)
5. **Exports everything** to structured directories

## Installation

```bash
pip install -e .
```

## Setup

```bash
# Authenticate with NotebookLM (opens browser)
article-factory login

# Check auth status
article-factory auth
```

## Quick Start

```bash
# Create a topic
article-factory create --topic "Machine Learning" --prompt "Write about ML fundamentals"

# Run full async pipeline (returns task_id immediately)
article-factory run 1 --prompt "Write about ML fundamentals"

# Check status
article-factory status                    # All topics
article-factory status <task-id>           # Specific task

# Cancel a running task
article-factory cancel <task-id>
```

## Commands

| Command | Description |
|---------|-------------|
| `login` | Authenticate with NotebookLM via browser |
| `auth` | Check authentication status |
| `create` | Create a new topic |
| `run` | Run full async pipeline (returns task_id immediately) |
| `status` | Show status of topics/tasks (with `--json` for structured output) |
| `retry` | Retry a failed topic |
| `cancel` | Cancel a running task |
| `version` | Show version |

## Output Structure

```
YYYY-MM-DD/topic-slug/
├── research_synthesis.md  # Research findings from deep research
├── article.md            # Generated article (from synthesis)
└── metadata.json          # Processing metadata
```

## Features

- **Async Pipeline**: Non-blocking execution with task IDs
- **Dynamic Prompting**: Inject prompts inline (`--prompt`) or from files (`--prompt-file`)
- **Source Citations**: Generated content cites sources from your notebook
- **Safety Constraints**: Built-in content safety checks
- **Error Resilience**: Rate limiting, circuit breaker, and automatic retries
- **Crash Recovery**: Resume from where you left off
- **JSON Output**: `--json` flag for automation

## Current Status

### v1.0 MVP - SHIPPED ✅

All core features working:
- CLI commands (create, status, retry, cancel)
- Notebook creation with timestamped slug format
- Deep research triggering
- Research synthesis generation
- Article generation (via synthesis fallback)
- SQLite state management

### v1.1 Async Pipeline - IN PROGRESS 🚧

Async execution with progress tracking:
- `run` command returns task_id immediately ✅
- `status <task-id>` shows progress ✅
- `cancel <task-id>` works ✅
- Progress notifications ⚠️ (partially)
- Article generation via synthesis ✅ (935 words)

**Known Limitations:**
- Source auto-import requires notebooklm-py >= 0.2.0
- Full article generation needs sources in notebook
- Media generation (infographic/audio) pending testing

See `.planning/STATE.md` for full roadmap.

## Requirements

- Python 3.9+
- NotebookLM account
- `pip install "notebooklm-py[browser]"` for authentication
- See `pyproject.toml` for full dependencies

## License

MIT
