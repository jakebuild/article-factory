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

**v2.0: Test Coverage**

- [ ] INFRA-01: pytest with asyncio support configured and runnable
- [ ] INFRA-02: NotebookLM SDK fully mocked (no real API calls in tests)
- [ ] INFRA-03: Test database fixtures (in-memory SQLite, seeded topics)
- [ ] INFRA-04: Coverage reporting configured (pytest-cov, target ≥70%)
- [ ] DB-01: Topic CRUD and retrieval tested
- [ ] DB-02: Topic status transitions tested
- [ ] DB-03: get_topic returns None for unknown ID
- [ ] DB-04: Async DB sessions work in test context
- [ ] PIPE-01: run_pipeline_async creates task and spawns subprocess
- [ ] PIPE-02: _execute_pipeline processes stages in correct order
- [ ] PIPE-03: Pipeline marks topic FAILED when a stage raises
- [ ] PIPE-04: Retry logic increments count and re-queues up to max retries
- [ ] RES-01: run_research starts, polls, and imports sources
- [ ] RES-02: Research polling raises error on timeout
- [ ] RES-03: generate_synthesis returns content string (not file path)
- [ ] RES-04: generate_synthesis content includes sources and summary
- [ ] CONTENT-01: apply_safety_constraints raises ValueError for disallowed patterns
- [ ] CONTENT-02: enforce_source_citations raises ValueError for unknown citations
- [ ] CONTENT-03: validate_article_length returns False outside word range
- [ ] CONTENT-04: generate_article uses report format by default
- [ ] CONTENT-05: get_output_dir resolves topic_name correctly for dict and object
- [ ] CONTENT-06: generate_infographic returns existing path without re-generating
- [ ] ERR-01: rate_limiter blocks beyond concurrent limit
- [ ] ERR-02: circuit_breaker opens after threshold failures
- [ ] ERR-03: circuit_breaker resets after cooldown
- [ ] NLM-01: generate_infographic deletes FAILED artifacts before triggering
- [ ] NLM-02: generate_infographic detects new artifact via before/after diff
- [ ] NLM-03: generate_infographic polls until ArtifactStatus.COMPLETED
- [ ] NLM-04: generate_infographic raises RuntimeError on ArtifactStatus.FAILED
- [ ] NLM-05: generate_infographic raises RuntimeError on timeout

### Out of Scope

Confirmed still out of scope:

- External API integrations beyond NotebookLM
- Web crawling or manual source import
- Hard-coded article templates (all prompts user-defined)
- Real-time collaboration features
- Multi-user accounts

## Current Milestone: v2.0 Test Coverage

**Goal:** Retroactively add a pytest test suite with mocked NotebookLM API, covering all critical business logic at ≥70% coverage — so bugs are caught in tests before live runs.

**Target areas:**
- Test infrastructure (pytest-asyncio, SDK mocks, DB fixtures, coverage)
- Database operations (CRUD, status transitions)
- Pipeline/scheduler (subprocess spawning, stage execution, retry logic)
- Research module (research triggering, synthesis content)
- Content generation (article safety, citations, media idempotency, output paths)
- Errors module (rate limiter, circuit breaker)
- NotebookLM wrapper (infographic polling, artifact diff, status detection)

## Current State (v1.1 SHIPPED)

**v1.0 Shipped:** 2026-02-12 | **v1.1 Shipped:** 2026-02-13
**Tech Stack:** Python + NotebookLMClient SDK
**LOC:** ~2,800 Python (after v1.1)
**Phases:** 4 complete (phases 1-4)
**Plans:** 12 executed
**Requirements:** 45/45 implemented

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

*Last updated: 2026-02-22 after v2.0 milestone started*
