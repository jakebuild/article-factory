# NotebookLM Article Factory

## What This Is

A fully autonomous, CLI-based research and content intelligence engine powered entirely by NotebookLM APIs. It performs AI-powered deep research, automatically imports discovered sources, and generates long-form publish-ready articles, infographic images, and executive audio briefings—persisting all notebooks for long-term knowledge compounding.

## Core Value

A programmable research-backed publishing engine that separates stable research from fully programmable writing, enabling dynamic prompt injection at runtime.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Create isolated notebooks per topic with timestamped slug format
- [ ] Trigger async deep research via NotebookLM API
- [ ] Poll and wait for research artifact completion (45min timeout)
- [ ] Generate structured research synthesis
- [ ] Generate long-form article using user-provided dynamic prompt (2,000-2,500 words)
- [ ] Generate infographic image from notebook context
- [ ] Generate executive audio briefing (8-10 minutes)
- [ ] Export all artifacts locally with structured output format
- [ ] Preserve notebooks permanently for knowledge compounding
- [ ] Support dynamic prompt injection via inline, file, or named templates

### Out of Scope

- External API integrations beyond NotebookLM
- Web crawling or manual source import
- Hard-coded article templates (all prompts user-defined)
- Real-time collaboration features
- Multi-user accounts

## Context

The system uses the NotebookLMClient Python SDK exclusively. All interactions flow through the SDK—no shell CLI calls to notebooklm binary. The architecture separates the research layer (stable, async) from the writing layer (fully programmable, prompt-driven).

## Constraints

- **Tech Stack**: Python + NotebookLMClient SDK only
- **APIs**: NotebookLM API exclusively—no external services
- **Concurrency**: Max 3 concurrent topics, 2-5 min poll interval
- **Timeout**: 45 minutes per artifact, max 2 retries per stage
- **Output Format**: Structured `YYYY-MM-DD/topic-slug/` directories

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| CLI-only interface | Simplicity, automation-friendly, no GUI overhead | — Pending |
| SQLite state store | Crash recovery, retry management, idempotent operations | — Pending |
| Dynamic prompt architecture | Flexibility for content experimentation and A/B testing | — Pending |
| Max 3 concurrent topics | Balance throughput with API rate limits | — Pending |

---
*Last updated: 2026-02-12 after initialization*
