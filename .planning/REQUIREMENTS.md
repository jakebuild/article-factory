# Requirements: NotebookLM Article Factory v1.1

**Defined:** 2026-02-12
**Core Value:** A programmable research-backed publishing engine that separates stable research from fully programmable writing, enabling dynamic prompt injection at runtime.

## v1.1 Requirements

### Async Task Execution

- [ ] **ASYNC-01**: `run` command triggers full pipeline and returns task_id immediately (non-blocking)
- [ ] **ASYNC-02**: `status <task-id>` returns task progress and current stage
- [ ] **ASYNC-03**: Pipeline stages: NOTEBOOK_CREATED → RESEARCH_TRIGGERED → RESEARCH_COMPLETED → SYNTHESIS_DONE → ARTICLE_DONE → MEDIA_DONE → COMPLETED
- [ ] **ASYNC-04**: User notified when task completes (stdout/stdout) with output location
- [ ] **ASYNC-05**: `cancel <task-id>` to cancel pending/running task

### Progress Notifications

- [ ] **NOTIFY-01**: Progress updates during long operations (research polling, article generation)
- [ ] **NOTIFY-02**: Clear stage indicators in status output

### Output Structure

- [ ] **OUT-07**: Output directory configurable via `--output-dir` flag

## v1 Requirements (from v1.0 - COMPLETED)

All v1.0 requirements archived at `.planning/milestones/v1.0-REQUIREMENTS.md`

## v2 Requirements (Deferred)

### Advanced Features

- **MCP-01**: MCP server integration for AI agent compatibility
- **MCP-02**: MCP protocol support for autonomous agent workflows
- **VID-01**: Video generation from notebook context
- **QUIZ-01**: Quiz generation from research synthesis
- **FLASH-01**: Flashcard generation from key insights

### Content Formats

- **NEWS-01**: Newsletter-style deep dive format
- **SEO-01**: SEO-optimized article templates
- **COMP-01**: Competitive analysis report format
- **CONT-01**: Contrarian thought leadership format

### Orchestration

- **BATCH-01**: Advanced batch scheduling with priority queues
- **PARA-01**: Configurable concurrency limits per domain
- **CACHE-01**: Content caching for repeated topics
- **DEDUP-01**: Duplicate topic detection

## Out of Scope

| Feature | Reason |
|---------|--------|
| External API integrations | Beyond NotebookLM scope |
| Web crawling | NotebookLM handles source discovery internally |
| Hard-coded templates | Dynamic prompt architecture enables flexibility |
| Real-time collaboration | CLI automation focus |
| Multi-user accounts | Single-user focus |
| Built-in web UI | CLI-first design philosophy |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ASYNC-01 | TBD | Planned |
| ASYNC-02 | TBD | Planned |
| ASYNC-03 | TBD | Planned |
| ASYNC-04 | TBD | Planned |
| ASYNC-05 | TBD | Planned |
| NOTIFY-01 | TBD | Planned |
| NOTIFY-02 | TBD | Planned |
| OUT-07 | TBD | Planned |

---

*Requirements defined: 2026-02-12*
*Last updated: 2026-02-12 for v1.1*
