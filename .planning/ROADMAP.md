# Roadmap: NotebookLM Article Factory

**Created:** 2026-02-12
**Depth:** Quick (3-5 phases)

A programmable research-backed publishing engine that separates stable research from fully programmable writing, enabling dynamic prompt injection at runtime.

---

## Phase Overview

| Phase | Goal | Requirements |
|-------|------|--------------|
| 1 - Foundation | User can install CLI and manage topic lifecycle with persistent state | CLI-01, CLI-02, CLI-04, CLI-05, CLI-07, STATE-01, STATE-02, STATE-03, STATE-04 |
| 2 - Research Layer | System creates notebooks, runs research, and handles core API errors | NOTE-01, NOTE-02, NOTE-03, NOTE-04, NOTE-05, ERR-01, ERR-02, STATE-05 |
| 3 - Content Delivery | System generates articles, media, and exports all artifacts with dynamic prompting | CLI-03, CLI-06, CONT-01, CONT-02, CONT-03, CONT-04, CONT-05, PROMPT-01, PROMPT-02, PROMPT-03, PROMPT-04, OUT-01, OUT-02, OUT-03, OUT-04, OUT-05, OUT-06, ERR-03, ERR-04, ERR-05 |

---

## Phase 1: Foundation

**Goal:** User can install CLI and manage topic lifecycle with persistent state

**Dependencies:** None (this is the starting phase)

**Requirements (9 total):**
- CLI-01: User can install article-factory via pip
- CLI-02: User can create a new topic via `article-factory create --topic "..." --prompt "..."`
- CLI-04: User can check status of all topics via `article-factory status`
- CLI-05: User can retry failed topics via `article-factory retry <id>`
- CLI-07: CLI provides progress feedback during long operations
- STATE-01: System persists topic metadata in SQLite database
- STATE-02: System tracks notebook_id, artifact_ids, and status per topic
- STATE-03: System supports crash recovery (idempotent operations)
- STATE-04: System maintains retry_count for failed operations

**Plans:** 2 plans in 2 waves

**Plan 01:** Project Setup + State Management
- Creates Poetry project structure with pyproject.toml
- Defines SQLAlchemy Topic model with state machine
- Implements SQLite database with crash recovery support
- Wave: 1 (no dependencies)

**Plan 02:** CLI Commands
- Implements Typer CLI application with create, status, retry commands
- Adds progress feedback during operations
- Wave: 2 (depends on Plan 01)

**Success Criteria:**

1. **Installation works:** User runs `pip install article-factory` and the CLI becomes available via `article-factory` command

2. **Topic creation works:** User runs `article-factory create --topic "machine learning" --prompt "Write about ML"` and a new topic is created with status "NEW"

3. **Status tracking works:** User runs `article-factory status` and sees all topics with their current status (NEW, PENDING, PROCESSING, COMPLETED, FAILED)

4. **Retry mechanism works:** User runs `article-factory retry <topic-id>` and failed topics are re-queued with incremented retry_count

5. **State persistence works:** After system restart, all topic metadata (notebook_id, artifact_ids, status) is preserved in SQLite database

6. **Crash recovery works:** If the system crashes mid-operation, topics can be resumed from their last stable state without data loss

---

## Phase 2: Research Layer

**Goal:** System creates notebooks, runs async research, and handles core API errors

**Dependencies:** Phase 1 complete (state management and topic creation required)

**Requirements (8 total):**
- NOTE-01: System can create isolated notebook with timestamped slug format (YYYY-MM-DD__topic-slug)
- NOTE-02: System triggers async deep research via NotebookLM API
- NOTE-03: System polls for research artifact completion (45min timeout)
- NOTE-04: System generates structured research synthesis
- NOTE-05: System preserves notebooks permanently for knowledge compounding
- ERR-01: System implements rate limiting to prevent API key suspension
- ERR-02: System implements circuit breaker pattern for API failures
- STATE-05: Database uses WAL mode for concurrent async access

**Success Criteria:**

1. **Notebook creation works:** System creates a notebook with format `YYYY-MM-DD__topic-slug` and stores notebook_id in database

2. **Research triggering works:** System successfully triggers async deep research via NotebookLM API and topic status transitions from PENDING to PROCESSING

3. **Polling completion works:** System polls for research completion, handles 45-minute timeout, and topic status reflects completion

4. **Synthesis generation works:** Research synthesis is generated and stored in the notebook for future reference

5. **Rate limiting works:** API calls are rate-limited to prevent key suspension (respects max 3 concurrent topics, 2-5 min poll interval)

6. **Circuit breaker works:** When API failures exceed threshold, circuit breaker prevents further calls and provides clear error messaging

7. **Concurrent access works:** WAL mode enables multiple async operations to access database without locking conflicts

**Plans:** 2 plans in 2 waves

**Plan 01:** NotebookLM Integration
- Integrates notebooklm-py SDK for NotebookLM API access
- Implements notebook CRUD operations with slug format (YYYY-MM-DD__topic-slug)
- Enables WAL mode for concurrent async access
- User setup: Authenticate with NotebookLM (run `notebooklm login`)
- Wave: 1 (no dependencies)

**Plan 02:** Research Orchestration
- Implements research workflow (trigger → poll → synthesis)
- Adds rate limiting (max 3 concurrent, 2 min interval)
- Adds circuit breaker for API failures
- Wave: 2 (depends on Plan 01)

---

## Phase 3: Content Delivery

**Goal:** System generates articles, media, and exports all artifacts with dynamic prompting

**Dependencies:** Phase 2 complete (research artifacts required for content generation)

**Requirements (20 total):**
- CLI-03: User can batch process topics from a file via `article-factory batch topics.txt`
- CLI-06: CLI provides structured output (JSON mode available via flag)
- CONT-01: System generates long-form article using user-provided dynamic prompt
- CONT-02: Generated articles are 2,000-2,500 words (default)
- CONT-03: Generated articles cite sources from notebook
- CONT-04: System generates infographic image from notebook context
- CONT-05: System generates executive audio briefing (8-10 minutes)
- PROMPT-01: User can inject prompts inline via --prompt flag
- PROMPT-02: User can provide prompts via file with --prompt-file
- PROMPT-03: System applies safety constraints to user prompts
- PROMPT-04: System enforces source-only citations in generated content
- OUT-01: System exports all artifacts to structured output directory
- OUT-02: Output format: YYYY-MM-DD/topic-slug/research_synthesis.md
- OUT-03: Output format: YYYY-MM-DD/topic-slug/article.md
- OUT-04: Output format: YYYY-MM-DD/topic-slug/infographic.png
- OUT-05: Output format: YYYY-MM-DD/topic-slug/podcast.mp3
- OUT-06: Output format: YYYY-MM-DD/topic-slug/metadata.json
- ERR-03: System retries failed operations (max 2 retries)
- ERR-04: System logs all failures with context for debugging
- ERR-05: System marks unrecoverable failures as FAILED status

**Success Criteria:**

1. **Batch processing works:** User runs `article-factory batch topics.txt` and all topics in the file are processed sequentially

2. **JSON output works:** User runs `article-factory status --json` and receives structured JSON output with topic details

3. **Dynamic prompting works:** User provides prompt via `--prompt "..."` or `--prompt-file prompt.txt` and the generated content reflects the custom prompt

4. **Article generation works:** Long-form article (2,000-2,500 words) is generated using user prompt and cites sources from notebook

5. **Infographic generation works:** Infographic image is generated from notebook context and saved as PNG

6. **Audio briefing works:** Executive audio briefing (8-10 minutes) is generated from notebook content and saved as MP3

7. **Structured export works:** All artifacts are exported to `YYYY-MM-DD/topic-slug/` directory with research_synthesis.md, article.md, infographic.png, podcast.mp3, and metadata.json

8. **Retry logic works:** Failed content generation operations are retried up to 2 times before final failure

9. **Error logging works:** All failures are logged with sufficient context (topic_id, operation, error details) for debugging

10. **Status accuracy works:** Unrecoverable failures are marked as FAILED status after exhausting retries

**Plans:** 3 plans in 2 waves (to be planned)

**Plan 01:** Article Generation & Dynamic Prompting
- Implements article generation using NotebookLM API with user-provided prompts
- Supports inline prompts (--prompt) and file-based prompts (--prompt-file)
- Enforces source-only citations and safety constraints
- Wave: 1 (depends on Phase 2 complete)

**Plan 02:** Media Generation
- Implements infographic image generation from notebook context
- Implements executive audio briefing generation (8-10 minutes)
- Wave: 2 (depends on Plan 01)

**Plan 03:** Output & Error Handling
- Implements structured output directory creation and artifact export
- Adds batch processing for multiple topics
- Adds JSON output mode for CLI
- Implements retry logic (max 2 retries) and error logging
- Wave: 2 (depends on Plan 01)

---

## Progress

| Phase | Status | Plans |
|-------|--------|-------|
| 1 - Foundation | ✓ Complete | 01-setup, 02-cli |
| 2 - Research Layer | ✓ Complete | 01-notebook, 02-research |
| 3 - Content Delivery | Planned | 03-article, 03-media, 03-output |

**Total:** 37 requirements across 3 phases

---

## Next Steps

Execute Phase 1 plans:
- Execute: `/gsd-execute-phase 1` (runs all plans)
- Or individually: `/gsd-execute-phase 1 --plan 01` then `/gsd-execute-phase 1 --plan 02`
