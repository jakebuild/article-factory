# NotebookLM Article Factory

A **programmable research-backed publishing engine** powered entirely by NotebookLM APIs. It separates stable research from fully programmable writing, enabling dynamic prompt injection at runtime.

## What It Does

1. **Authenticates** with NotebookLM via browser login
2. **Creates notebooks** on NotebookLM from your topics
3. **Runs deep research** automatically on each topic
4. **Generates content** using your custom prompts:
   - Research synthesis from discovered sources
   - Long-form articles (2,000-2,500 words)
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
├── article.md            # Generated article (2,000-2,500 words)
├── infographic.png      # Generated infographic (optional)
├── podcast.mp3          # Generated audio briefing (optional)
└── metadata.json         # Processing metadata
```

## Features

- **Async Pipeline**: Non-blocking execution with task IDs and progress tracking
- **Dynamic Prompting**: Inject prompts inline (`--prompt`) or from files (`--prompt-file`)
- **Source Citations**: Generated content cites sources from your notebook
- **Safety Constraints**: Built-in content safety checks
- **Error Resilience**: Rate limiting, circuit breaker, and automatic retries
- **Crash Recovery**: Resume from where you left off
- **JSON Output**: `--json` flag for automation
- **Report Format**: `--format synthesis|report` for different article generation methods

## Current Status

### v1.1 Async Pipeline - SHIPPED ✅

Full async execution with progress tracking:

- `run` command returns task_id immediately ✅
- `status <task-id>` shows progress ✅
- `cancel <task-id>` works ✅
- Source discovery and import ✅ (39 sources found, 10 imported)
- Article generation ✅ (2,356 words via chat API)
- `--format synthesis|report` option ✅
- Media generation fixes ✅ (rate limiter bug resolved)

**Verified:** 11 UAT tests passed, 0 issues

### v2.0 Planning

Extended formats and MCP integration:
- MCP server integration
- Quiz/flashcard generation
- Newsletter/SEO templates

## Requirements

- Python 3.11+
- NotebookLM account
- Run `source .venv/bin/activate` to use the included environment
- See `pyproject.toml` for full dependencies

## License

MIT
