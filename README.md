# NotebookLM Article Factory

A **programmable research-backed publishing engine** powered entirely by NotebookLM APIs. It separates stable research from fully programmable writing, enabling dynamic prompt injection at runtime.

## What It Does

1. **Creates notebooks** on NotebookLM from your topics
2. **Runs deep research** automatically on each topic
3. **Generates content** using your custom prompts:
   - Long-form articles (2,000-2,500 words)
   - Infographic images
   - Executive audio briefings (8-10 minutes)
4. **Exports everything** to structured directories

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# Create a topic
article-factory create --topic "Machine Learning" --prompt "Write about ML fundamentals"

# Run research
article-farticle research 1

# Generate article with custom prompt
article-factory article 1 --prompt "Write a beginner-friendly guide"

# Or batch process multiple topics
article-factory batch topics.txt --prompt "Write about {topic}"
```

## Commands

| Command | Description |
|---------|-------------|
| `create` | Create a new topic for article generation |
| `status` | Show status of all topics (with `--json` for structured output) |
| `retry` | Retry a failed topic |
| `article` | Generate article from research (requires `--prompt` or `--prompt-file`) |
| `batch` | Process multiple topics from a file |
| `version` | Show version |

## Output Structure

```
YYYY-MM-DD/topic-slug/
├── research_synthesis.md  # Research findings
├── article.md             # Generated article
├── infographic.png        # Generated image
├── podcast.mp3            # Audio briefing (8-10 min)
└── metadata.json          # Processing metadata
```

## Features

- **Dynamic Prompting**: Inject prompts inline (`--prompt`) or from files (`--prompt-file`)
- **Source Citations**: Generated content cites sources from your notebook
- **Safety Constraints**: Built-in content safety checks
- **Error Resilience**: Rate limiting, circuit breaker, and automatic retries
- **Crash Recovery**: Resume from where you left off
- **JSON Output**: `--json` flag for automation

## Requirements

- Python 3.9+
- NotebookLM API credentials
- See `pyproject.toml` for full dependencies

## License

MIT
