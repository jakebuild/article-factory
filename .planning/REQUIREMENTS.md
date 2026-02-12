# Requirements: NotebookLM Article Factory

**Defined:** 2026-02-12
**Core Value:** A programmable research-backed publishing engine that separates stable research from fully programmable writing, enabling dynamic prompt injection at runtime.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### CLI Foundation

- [ ] **CLI-01**: User can install article-factory via pip
- [ ] **CLI-02**: User can create a new topic via `article-factory create --topic "..." --prompt "..."`
- [ ] **CLI-03**: User can batch process topics from a file via `article-factory batch topics.txt`
- [ ] **CLI-04**: User can check status of all topics via `article-factory status`
- [ ] **CLI-05**: User can retry failed topics via `article-factory retry <id>`
- [ ] **CLI-06**: CLI provides structured output (JSON mode available via flag)
- [ ] **CLI-07**: CLI provides progress feedback during long operations

### State Management

- [ ] **STATE-01**: System persists topic metadata in SQLite database
- [ ] **STATE-02**: System tracks notebook_id, artifact_ids, and status per topic
- [ ] **STATE-03**: System supports crash recovery (idempotent operations)
- [ ] **STATE-04**: System maintains retry_count for failed operations
- [ ] **STATE-05**: Database uses WAL mode for concurrent async access

### Notebook Operations

- [ ] **NOTE-01**: System can create isolated notebook with timestamped slug format (YYYY-MM-DD__topic-slug)
- [ ] **NOTE-02**: System triggers async deep research via NotebookLM API
- [ ] **NOTE-03**: System polls for research artifact completion (45min timeout)
- [ ] **NOTE-04**: System generates structured research synthesis
- [ ] **NOTE-05**: System preserves notebooks permanently for knowledge compounding

### Content Generation

- [ ] **CONT-01**: System generates long-form article using user-provided dynamic prompt
- [ ] **CONT-02**: Generated articles are 2,000-2,500 words (default)
- [ ] **CONT-03**: Generated articles cite sources from notebook
- [ ] **CONT-04**: System generates infographic image from notebook context
- [ ] **CONT-05**: System generates executive audio briefing (8-10 minutes)

### Dynamic Prompting

- [ ] **PROMPT-01**: User can inject prompts inline via --prompt flag
- [ ] **PROMPT-02**: User can provide prompts via file with --prompt-file
- [ ] **PROMPT-03**: System applies safety constraints to user prompts
- [ ] **PROMPT-04**: System enforces source-only citations in generated content

### Output & Export

- [ ] **OUT-01**: System exports all artifacts to structured output directory
- [ ] **OUT-02**: Output format: YYYY-MM-DD/topic-slug/research_synthesis.md
- [ ] **OUT-03**: Output format: YYYY-MM-DD/topic-slug/article.md
- [ ] **OUT-04**: Output format: YYYY-MM-DD/topic-slug/infographic.png
- [ ] **OUT-05**: Output format: YYYY-MM-DD/topic-slug/podcast.mp3
- [ ] **OUT-06**: Output format: YYYY-MM-DD/topic-slug/metadata.json

### Error Handling

- [ ] **ERR-01**: System implements rate limiting to prevent API key suspension
- [ ] **ERR-02**: System implements circuit breaker pattern for API failures
- [ ] **ERR-03**: System retries failed operations (max 2 retries)
- [ ] **ERR-04**: System logs all failures with context for debugging
- [ ] **ERR-05**: System marks unrecoverable failures as FAILED status

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

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

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| External API integrations | Beyond NotebookLM scope—complexity without user value |
| Web crawling | NotebookLM handles source discovery internally |
| Hard-coded templates | Dynamic prompt architecture enables flexibility |
| Real-time collaboration | Not aligned with CLI automation focus |
| Multi-user accounts | Single-user focus for personal knowledge compounding |
| Built-in web UI | CLI-first design philosophy |
| Browser-based scraping | NotebookLM API handles source import |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CLI-01 | Phase 1 | Pending |
| CLI-02 | Phase 1 | Pending |
| CLI-04 | Phase 1 | Pending |
| CLI-05 | Phase 1 | Pending |
| CLI-07 | Phase 1 | Pending |
| STATE-01 | Phase 1 | Pending |
| STATE-02 | Phase 1 | Pending |
| STATE-03 | Phase 1 | Pending |
| STATE-04 | Phase 1 | Pending |
| NOTE-01 | Phase 2 | Pending |
| NOTE-02 | Phase 2 | Pending |
| NOTE-03 | Phase 2 | Pending |
| NOTE-04 | Phase 2 | Pending |
| NOTE-05 | Phase 2 | Pending |
| ERR-01 | Phase 2 | Pending |
| ERR-02 | Phase 2 | Pending |
| STATE-05 | Phase 2 | Pending |
| CLI-03 | Phase 3 | Pending |
| CLI-06 | Phase 3 | Pending |
| CONT-01 | Phase 3 | Pending |
| CONT-02 | Phase 3 | Pending |
| CONT-03 | Phase 3 | Pending |
| CONT-04 | Phase 3 | Pending |
| CONT-05 | Phase 3 | Pending |
| PROMPT-01 | Phase 3 | Pending |
| PROMPT-02 | Phase 3 | Pending |
| PROMPT-03 | Phase 3 | Pending |
| PROMPT-04 | Phase 3 | Pending |
| OUT-01 | Phase 3 | Pending |
| OUT-02 | Phase 3 | Pending |
| OUT-03 | Phase 3 | Pending |
| OUT-04 | Phase 3 | Pending |
| OUT-05 | Phase 3 | Pending |
| OUT-06 | Phase 3 | Pending |
| ERR-03 | Phase 3 | Pending |
| ERR-04 | Phase 3 | Pending |
| ERR-05 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 37 total
- Mapped to phases: 37
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-12*
*Last updated: 2026-02-12 after initial definition*
