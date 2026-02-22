# Roadmap: NotebookLM Article Factory

**Last Updated:** 2026-02-22

---

## Milestones

- ✅ **v1.0 MVP** — Phases 1-3 (shipped 2026-02-12)
- ✅ **v1.1 Async Task Execution** — Phases 1-4 (shipped 2026-02-13)
- 🚧 **v2.0 Test Coverage** — Phases 5-8 (in progress)

---

<details>
<summary>✅ v1.1 Async Task Execution (Phases 1-4) — SHIPPED 2026-02-13</summary>

- [x] Phase 1: Foundation (2/2 plans) — 2026-02-12
- [x] Phase 2: Research Layer (2/2 plans) — 2026-02-12
- [x] Phase 3: Content Delivery (3/3 plans) — 2026-02-12
- [x] Phase 4: Async Pipeline (5/5 plans) — 2026-02-13

</details>

---

## 🚧 v2.0: Test Coverage (In Progress)

**Milestone Goal:** Retroactive pytest suite with mocked NotebookLM SDK covering all critical business logic at ≥70% code coverage — so bugs are caught in tests before live runs.

### Phases

- [ ] **Phase 5: Test Infrastructure** - pytest-asyncio setup, SDK mocks, DB fixtures, coverage config
- [ ] **Phase 6: Database + Errors Tests** - Core state layer CRUD, status transitions, and resilience primitives
- [ ] **Phase 7: Pipeline + Research Tests** - Async pipeline execution, stage ordering, retry logic, research orchestration
- [ ] **Phase 8: Content + Wrapper Tests** - Article generation logic, safety constraints, media idempotency, NLM infographic wrapper

---

## Phase Details

### Phase 5: Test Infrastructure
**Goal**: Developer can run the full test suite against mocked APIs with coverage reporting in one command
**Depends on**: Phase 4 (codebase complete)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04
**Success Criteria** (what must be TRUE):
  1. `pytest` runs to completion without NotebookLM credentials and all tests pass
  2. NotebookLM SDK (client, artifacts, research, chat APIs) is fully replaceable via a fixture — no real HTTP calls are made
  3. Each test gets an isolated in-memory SQLite database pre-seeded with topic rows
  4. `pytest --cov` produces a coverage report showing overall coverage ≥70%
**Plans**: 1 plan

Plans:
- [ ] 05-01-PLAN.md — pytest config, in-memory DB fixture, SDK mock fixture, coverage validation

### Phase 6: Database + Errors Tests
**Goal**: Database CRUD, status transitions, and resilience primitives (rate limiter, circuit breaker) are verified in isolation
**Depends on**: Phase 5
**Requirements**: DB-01, DB-02, DB-03, DB-04, ERR-01, ERR-02, ERR-03
**Success Criteria** (what must be TRUE):
  1. A topic created via the DB layer can be retrieved by ID with all fields intact
  2. Status transitions from NEW through PROCESSING to COMPLETED and FAILED are persisted correctly and readable back
  3. Querying an unknown topic ID returns None (no exception raised)
  4. Concurrent async DB operations complete without locking errors
  5. rate_limiter blocks a fourth concurrent caller when three slots are already held
  6. circuit_breaker opens after hitting the failure threshold and rejects subsequent calls; resets after cooldown elapses
**Plans**: TBD

Plans:
- [ ] 06-01: Database CRUD tests (DB-01..04)
- [ ] 06-02: Errors module tests — rate limiter and circuit breaker (ERR-01..03)

### Phase 7: Pipeline + Research Tests
**Goal**: Async pipeline stage execution and research orchestration are verified with mocked SDK and subprocess calls
**Depends on**: Phase 6
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-04, RES-01, RES-02, RES-03, RES-04
**Success Criteria** (what must be TRUE):
  1. run_pipeline_async creates a task record and spawns a detached subprocess (verified via mock)
  2. _execute_pipeline processes stages in the documented order from NOTEBOOK_CREATED to COMPLETED
  3. When any pipeline stage raises an exception, the topic is marked FAILED and the error is recorded
  4. Retry logic increments the retry count and re-queues the topic, and stops at the max retry limit
  5. run_research starts deep research, polls until complete, and imports discovered sources into the notebook
  6. Research polling raises a timeout error when max duration is exceeded without a completion signal
  7. generate_synthesis returns a string containing both discovered sources and a research summary section
**Plans**: TBD

Plans:
- [ ] 07-01: Pipeline scheduler tests (PIPE-01..04)
- [ ] 07-02: Research module tests (RES-01..04)

### Phase 8: Content + Wrapper Tests
**Goal**: Content generation helpers and the NotebookLM infographic wrapper are verified for correctness and idempotency
**Depends on**: Phase 7
**Requirements**: CONTENT-01, CONTENT-02, CONTENT-03, CONTENT-04, CONTENT-05, CONTENT-06, NLM-01, NLM-02, NLM-03, NLM-04, NLM-05
**Success Criteria** (what must be TRUE):
  1. apply_safety_constraints raises ValueError when a prompt matches a disallowed pattern
  2. enforce_source_citations raises ValueError when the article references sources not present in the notebook
  3. validate_article_length returns False for articles below the minimum or above the maximum word count
  4. generate_article defaults to report format without an explicit format argument
  5. get_output_dir resolves topic_name correctly whether the topic is a dict (from DB) or an ORM object
  6. generate_infographic returns the existing file path immediately without triggering SDK calls when the file already exists
  7. generate_infographic in the NLM wrapper deletes FAILED artifacts, detects new artifact via before/after diff, polls until COMPLETED, and raises RuntimeError on FAILED status or timeout
**Plans**: TBD

Plans:
- [ ] 08-01: Content generation helper tests (CONTENT-01..06)
- [ ] 08-02: NotebookLM wrapper infographic tests (NLM-01..05)

---

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.1 | 2/2 | Complete | 2026-02-12 |
| 2. Research Layer | v1.1 | 2/2 | Complete | 2026-02-12 |
| 3. Content Delivery | v1.1 | 3/3 | Complete | 2026-02-12 |
| 4. Async Pipeline | v1.1 | 5/5 | Complete | 2026-02-13 |
| 5. Test Infrastructure | v2.0 | 0/1 | Not started | - |
| 6. Database + Errors Tests | v2.0 | 0/2 | Not started | - |
| 7. Pipeline + Research Tests | v2.0 | 0/2 | Not started | - |
| 8. Content + Wrapper Tests | v2.0 | 0/2 | Not started | - |

---

_For v1.1 details, see `.planning/milestones/v1.1-ROADMAP.md`_
_For v1.0 details, see `.planning/milestones/v1.0-ROADMAP.md`_
