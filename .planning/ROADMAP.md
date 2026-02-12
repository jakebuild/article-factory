# Roadmap: NotebookLM Article Factory

**Last Updated:** 2026-02-12

---

## Milestones

- ✅ **v1.0 MVP** — Phases 1-3 (shipped 2026-02-12)
- 🚧 **v1.1** — Async Task Execution (Gap Closure)
- 📋 **v2.0** — Extended Formats (planned)

---

## v1.0 MVP (COMPLETED)

Phases 1-3 complete. All 37 requirements implemented.

**Archived:** See `.planning/milestones/v1.0-ROADMAP.md`

---

## v1.1: Async Task Execution

**Goal:** Non-blocking task execution with progress tracking and task IDs

**Dependencies:** Phase 3 complete

**Requirements:**
- ASYNC-01: `run` command returns task_id immediately (non-blocking)
- ASYNC-02: `status <task-id>` shows progress and stage
- ASYNC-03: Pipeline stages (NEW → NOTEBOOK_CREATED → RESEARCH_TRIGGERED → RESEARCH_COMPLETED → SYNTHESIS_DONE → ARTICLE_DONE → MEDIA_DONE → COMPLETED/FAILED)
- ASYNC-04: User notified on completion
- ASYNC-05: `cancel <task-id>` to cancel tasks
- NOTIFY-01/02: Progress notifications
- OUT-07: Configurable output directory

**Plans:** 5 plans in 2 waves (3 implementation + 1 gap closure + 1 upgrade)

**Plan 01:** Task Scheduler & Job Queue
- Implements task_id generation (UUID)
- Adds queue system for async job management
- Non-blocking `run` command that returns immediately
- Wave: 1

**Plan 02:** Progress Tracking & Notifications
- Pipeline stage tracking in database
- Progress updates during long operations
- User notification on completion
- Wave: 2

**Plan 03:** Status & Cancel Commands
- `status <task-id>` command with progress details
- `cancel <task-id>` command
- Configurable output directory
- Wave: 2

**Gap Closure Plan 04:** SDK Limitations Documentation
- Document notebooklm-py SDK v0.1.1 limitations
- Diagnose media generation rate_limiter issue
- Update UAT with final gap status
- Wave: 1

**Plan 05:** SDK Upgrade & Report-Based Articles
- Upgrade Python to 3.10+ (enables notebooklm-py 0.2.0+)
- Upgrade notebooklm-py to 0.3.2
- Replace chat.ask() with generate_report() for articles
- Add --format synthesis|report CLI option
- Wave: 1

**Success Criteria:**

1. **Non-blocking run works:** User runs `article-factory run <topic-id>` and gets task_id immediately without waiting

2. **Status tracking works:** User runs `article-factory status <task-id>` and sees current pipeline stage

3. **Completion notification works:** User receives notification when task completes with output location

4. **Cancel works:** User can cancel pending/running task with `article-factory cancel <task-id>`

5. **Progress updates work:** User sees progress during research polling and article generation

---

## v2.0 (Planned)

**Goal:** Extended content formats and MCP integration

- MCP server integration
- Quiz/flashcard generation
- Newsletter/SEO templates

---

## Progress

| Phase | Milestone | Status | Plans |
|-------|-----------|--------|-------|
| 1 | v1.0 | Complete | 2/2 |
| 2 | v1.0 | Complete | 2/2 |
| 3 | v1.0 | Complete | 3/3 |
| 4 | v1.1 | Gap Closure + Upgrade | 4/5 |

---

*For v1.0 details, see `.planning/milestones/v1.0-ROADMAP.md*
