# Requirements: NotebookLM Article Factory

**Defined:** 2026-02-22
**Milestone:** v2.0 Test Coverage
**Core Value:** A programmable research-backed publishing engine that separates stable research from fully programmable writing, enabling dynamic prompt injection at runtime.

## v2.0 Requirements

Retroactive test coverage for all critical business logic. All tests use mocked NotebookLM SDK — no real API calls. Target: ≥70% code coverage.

### Test Infrastructure

- [ ] **INFRA-01**: Developer can run `pytest` and all tests pass without NotebookLM credentials
- [ ] **INFRA-02**: NotebookLM SDK is fully mockable via fixtures (NotebookLMClientWrapper, artifacts, research, chat APIs)
- [ ] **INFRA-03**: Test database fixture provides isolated in-memory SQLite with seeded topics per test
- [ ] **INFRA-04**: Coverage report generated on `pytest --cov` showing ≥70% overall coverage

### Database

- [ ] **DB-01**: Topic can be created and retrieved by ID via get_topic
- [ ] **DB-02**: Topic status transitions (NEW → PROCESSING → COMPLETED / FAILED) are persisted correctly
- [ ] **DB-03**: get_topic returns None for an unknown topic ID
- [ ] **DB-04**: Async DB session operations complete without locking errors under concurrent access

### Pipeline / Scheduler

- [x] **PIPE-01**: run_pipeline_async creates a task record and spawns a detached subprocess
- [x] **PIPE-02**: _execute_pipeline processes pipeline stages in correct order (NOTEBOOK_CREATED → … → COMPLETED)
- [x] **PIPE-03**: Pipeline marks topic as FAILED and records error when any stage raises an exception
- [x] **PIPE-04**: Retry logic increments retry count and re-queues topic up to max retry limit

### Research

- [x] **RES-01**: run_research starts deep research, polls until complete, and imports discovered sources into notebook
- [x] **RES-02**: Research polling raises a timeout error when max duration is exceeded without completion
- [x] **RES-03**: generate_synthesis returns a content string, not a file path
- [x] **RES-04**: generate_synthesis content includes discovered source list and research summary section

### Content Generation

- [x] **CONTENT-01**: apply_safety_constraints raises ValueError when prompt matches a disallowed pattern
- [x] **CONTENT-02**: enforce_source_citations raises ValueError when article cites sources not present in notebook
- [x] **CONTENT-03**: validate_article_length returns False for articles below min or above max word count
- [x] **CONTENT-04**: generate_article defaults to report format (not synthesis/chat)
- [x] **CONTENT-05**: get_output_dir resolves topic_name correctly for both dict topics (from DB) and ORM object topics
- [x] **CONTENT-06**: generate_infographic returns existing file path immediately without triggering re-generation

### Errors

- [ ] **ERR-01**: rate_limiter blocks acquisition beyond the configured concurrent limit
- [ ] **ERR-02**: circuit_breaker opens after reaching the failure threshold and rejects subsequent calls
- [ ] **ERR-03**: circuit_breaker resets to closed state after the cooldown period elapses

### NotebookLM Wrapper

- [x] **NLM-01**: generate_infographic deletes all FAILED infographic artifacts before triggering new generation
- [x] **NLM-02**: generate_infographic identifies the newly created artifact via before/after artifact list diff
- [x] **NLM-03**: generate_infographic polls _list_raw until artifact reaches ArtifactStatus.COMPLETED and returns task_id
- [x] **NLM-04**: generate_infographic raises RuntimeError when artifact reaches ArtifactStatus.FAILED
- [x] **NLM-05**: generate_infographic raises RuntimeError when polling exceeds the timeout duration

## Previous Requirements (v1.0 + v1.1 — COMPLETED)

All v1.0 requirements archived at `.planning/milestones/v1.0-REQUIREMENTS.md`
All v1.1 requirements archived at `.planning/milestones/v1.1-REQUIREMENTS.md`

## Future Requirements (Deferred to v3.0)

### Extended Formats

- **MCP-01**: MCP server integration for AI agent compatibility
- **MCP-02**: MCP protocol support for autonomous agent workflows
- **QUIZ-01**: Quiz generation from research synthesis
- **FLASH-01**: Flashcard generation from key insights
- **NEWS-01**: Newsletter-style deep dive format
- **SEO-01**: SEO-optimized article templates

### CLI Tests (deferred from v2.0)

- **CLI-01**: `run` command returns task_id immediately
- **CLI-02**: `status` command displays current pipeline stage
- **CLI-03**: `graphic` command generates and saves infographic
- **CLI-04**: `article` command generates and saves article

## Out of Scope

| Feature | Reason |
|---------|--------|
| Live integration tests (real API) | Too slow and costly for CI; mocked tests sufficient |
| CLI command tests | Thin glue layer; business logic tested via unit tests |
| Performance/load tests | Not relevant to current quality goals |
| End-to-end pipeline tests against real NotebookLM | Covered by manual UAT |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 5 | Pending |
| INFRA-02 | Phase 5 | Pending |
| INFRA-03 | Phase 5 | Pending |
| INFRA-04 | Phase 5 | Pending |
| DB-01 | Phase 6 | Complete |
| DB-02 | Phase 6 | Complete |
| DB-03 | Phase 6 | Complete |
| DB-04 | Phase 6 | Complete |
| ERR-01 | Phase 6 | Complete |
| ERR-02 | Phase 6 | Complete |
| ERR-03 | Phase 6 | Complete |
| PIPE-01 | Phase 7 | Complete |
| PIPE-02 | Phase 7 | Complete |
| PIPE-03 | Phase 7 | Complete |
| PIPE-04 | Phase 7 | Complete |
| RES-01 | Phase 7 | Complete |
| RES-02 | Phase 7 | Complete |
| RES-03 | Phase 7 | Complete |
| RES-04 | Phase 7 | Complete |
| CONTENT-01 | Phase 8 | Complete |
| CONTENT-02 | Phase 8 | Complete |
| CONTENT-03 | Phase 8 | Complete |
| CONTENT-04 | Phase 8 | Complete |
| CONTENT-05 | Phase 8 | Complete |
| CONTENT-06 | Phase 8 | Complete |
| NLM-01 | Phase 8 | Complete |
| NLM-02 | Phase 8 | Complete |
| NLM-03 | Phase 8 | Complete |
| NLM-04 | Phase 8 | Complete |
| NLM-05 | Phase 8 | Complete |

**Coverage:**
- v2.0 requirements: 30 total
- Mapped to phases: 30
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-22*
*Last updated: 2026-02-22 — traceability populated during roadmap creation*
