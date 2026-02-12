# NotebookLM Article Factory

## What This Is

A fully autonomous, CLI-based research and content intelligence engine powered entirely by NotebookLM APIs. It performs AI-powered deep research, automatically imports discovered sources, and generates long-form publish-ready articles, infographic images, and executive audio briefings—persisting all notebooks for long-term knowledge compounding.

## Core Value

A programmable research-backed publishing engine that separates stable research from fully programmable writing, enabling dynamic prompt injection at runtime.

## Requirements

### Validated

All v1.0 requirements shipped and validated:

- [x] CLI commands: create, status, retry, article, batch, version
- [x] JSON output mode for structured data
- [x] SQLite state management with crash recovery
- [x] Notebook creation with timestamped slug format (YYYY-MM-DD__topic-slug)
- [x] Async deep research triggering via NotebookLM API
- [x] Research artifact polling with 45-minute timeout
- [x] Structured research synthesis generation
- [x] Notebook preservation for knowledge compounding
- [x] Long-form article generation (2,000-2,500 words) with custom prompts
- [x] Source citation enforcement in generated content
- [x] Infographic image generation from notebook context
- [x] Executive audio briefing generation (8-10 minutes)
- [x] Structured output directory (YYYY-MM-DD/topic-slug/)
- [x] Export formats: research_synthesis.md, article.md, infographic.png, podcast.mp3, metadata.json
- [x] Rate limiting (max 3 concurrent, 2-min interval)
- [x] Circuit breaker for API failures
- [x] Retry logic (max 2 retries)
- [x] Error logging with context
- [x] FAILED status for unrecoverable failures
- [x] Safety constraints for prompts

### Active

**v1.1: Async Task Execution**

- [ ] ASYNC-01: `run` command triggers full pipeline and returns task_id immediately
- [ ] ASYNC-02: `status <task-id>` returns task progress and current stage
- [ ] ASYNC-03: Pipeline stages: NOTEBOOK_CREATED → RESEARCH_TRIGGERED → RESEARCH_COMPLETED → SYNTHESIS_DONE → ARTICLE_DONE → MEDIA_DONE → COMPLETED
- [ ] ASYNC-04: User notified when task completes with output location
- [ ] ASYNC-05: `cancel <task-id>` to cancel pending/running task
- [ ] NOTIFY-01: Progress updates during long operations
- [ ] NOTIFY-02: Clear stage indicators in status output
- [ ] OUT-07: Configurable output directory via `--output-dir`

### Out of Scope

Confirmed still out of scope:

- External API integrations beyond NotebookLM
- Web crawling or manual source import
- Hard-coded article templates (all prompts user-defined)
- Real-time collaboration features
- Multi-user accounts

## Current State (v1.0 SHIPPED)

**Shipped:** 2026-02-12
**Tech Stack:** Python + NotebookLMClient SDK
**LOC:** ~2,029 Python
**Phases:** 3 complete
**Plans:** 7 executed
**Requirements:** 37/37 implemented

### CLI Commands

```bash
article-factory create --topic "..." --prompt "..."
article-factory status [--json]
article-factory retry <id>
article-factory article <id> [--prompt "..." | --prompt-file ...] [--json]
article-factory batch <topics-file> [--prompt "..." | --prompt-file ...] [--json]
article-factory version
```

### Output Structure

```
YYYY-MM-DD/topic-slug/
├── research_synthesis.md
├── article.md
├── infographic.png
├── podcast.mp3
└── metadata.json
```

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| CLI-only interface | Simplicity, automation-friendly, no GUI overhead | ✅ Confirmed |
| SQLite state store | Crash recovery, retry management, idempotent operations | ✅ Confirmed |
| Dynamic prompt architecture | Flexibility for content experimentation and A/B testing | ✅ Confirmed |
| Max 3 concurrent topics | Balance throughput with API rate limits | ✅ Confirmed |
| WAL mode for SQLite | Concurrent async access without locking | ✅ Confirmed |
| notebooklm-py SDK | Official SDK for NotebookLM API integration | ✅ Confirmed |
| Rate limiting + circuit breaker | API resilience and key protection | ✅ Confirmed |
| Research orchestration workflow | Async start/poll/run patterns for resilience | ✅ Confirmed |

## Context

The system uses the NotebookLMClient Python SDK exclusively. All interactions flow through the SDK—no shell CLI calls to notebooklm binary. The architecture separates the research layer (stable, async) from the writing layer (fully programmable, prompt-driven).

## Constraints

- **Tech Stack**: Python + NotebookLMClient SDK only
- **APIs**: NotebookLM API exclusively—no external services
- **Concurrency**: Max 3 concurrent topics, 2-5 min poll interval
- **Timeout**: 45 minutes per artifact, max 2 retries per stage
- **Output Format**: Structured `YYYY-MM-DD/topic-slug/` directories

---

*Last updated: 2026-02-12 after v1.0 milestone completion*
