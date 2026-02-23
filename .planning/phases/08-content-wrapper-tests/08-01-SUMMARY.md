---
phase: 08-content-wrapper-tests
plan: "01"
subsystem: testing
tags: [pytest, content-helpers, media, output-paths, idempotency]

# Dependency graph
requires:
  - phase: 07-pipeline-research-tests
    provides: stable research/pipeline behaviors and fixture-backed NotebookLM mocks
provides:
  - Deterministic CONTENT-01..CONTENT-04 coverage for article safety, citation, length, and default format behavior
  - Deterministic CONTENT-05 and CONTENT-06 coverage for media output path handling and infographic idempotent short-circuit
  - Topic-shape-safe `get_output_dir` support for dict and ORM-like topic objects with string/datetime `created_at`
affects: [08-02 wrapper tests, regression safety for article/media helpers]

# Tech tracking
tech-stack:
  added: []
  patterns: [requirement-mapped pytest naming, dict-or-attribute topic field resolution]

key-files:
  created: [tests/test_media.py, .planning/phases/08-content-wrapper-tests/08-01-SUMMARY.md]
  modified: [tests/test_article_generation.py, src/article_factory/media.py, tests/test_media.py, .planning/STATE.md]

key-decisions:
  - "Map each CONTENT-01..CONTENT-06 truth to explicit deterministic test assertions"
  - "Harden media output path resolution for both dict and attribute-based topic records"

patterns-established:
  - "Requirement IDs are reflected directly in test names for traceability"
  - "Output path builders must accept DB dict rows and ORM-like objects consistently"

# Metrics
duration: 3 min
completed: 2026-02-23
---

# Phase 8 Plan 1: Content Helper + Media Idempotency Summary

**Deterministic tests now enforce content safety/citation/length/default-format contracts and media output path/idempotent infographic behavior across dict and ORM-like topic shapes.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-23T04:10:31Z
- **Completed:** 2026-02-23T04:13:36Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Expanded `tests/test_article_generation.py` with requirement-mapped CONTENT-01..CONTENT-04 assertions.
- Created `tests/test_media.py` with CONTENT-05 output-dir coverage and CONTENT-06 existing-file infographic short-circuit coverage.
- Hardened `src/article_factory/media.py:get_output_dir` to resolve fields safely from dict and attribute-based topic shapes.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add CONTENT-01..CONTENT-04 tests for article helper contracts** - `5ca0698` (test)
2. **Task 2: Add CONTENT-05 and CONTENT-06 tests for media output resolution and idempotent infographic generation** - `57bfe32` (test)
3. **Task 3: Apply minimal source fixes required by failing content/media tests and run full slice verification** - `a26eaa4` (fix)

## Files Created/Modified
- `tests/test_article_generation.py` - added deterministic content helper contract tests for safety, citation validation, length bounds, and format default.
- `tests/test_media.py` - added media output-dir and infographic idempotency tests.
- `src/article_factory/media.py` - fixed topic/date extraction for dict and ORM-like objects before slug/path generation.

## Decisions Made
- Used direct helper-level assertions (ValueError/boolean/signature defaults) to keep CONTENT-01..CONTENT-04 tests fully offline and deterministic.
- Normalized topic field resolution in `get_output_dir` so tests and runtime support both dict-backed and ORM-style topic records.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed ORM topic compatibility in media output directory resolution**
- **Found during:** Task 3 (Apply minimal source fixes and run full slice verification)
- **Issue:** `get_output_dir` used dict-only access for `created_at`, which could fail for attribute-based topic objects.
- **Fix:** Added dict-or-attribute resolution for `topic` and `created_at`, including datetime-safe date formatting.
- **Files modified:** `src/article_factory/media.py`, `tests/test_media.py`
- **Verification:** `.venv/bin/python -m pytest tests/test_article_generation.py tests/test_media.py -v` and `.venv/bin/python -m pytest tests/ --cov=src/article_factory --cov-report=term-missing -v`
- **Committed in:** `a26eaa4`

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Auto-fix was required to make CONTENT-05 robust for real ORM-like topic records; no scope creep.

## Authentication Gates

None.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Content helper and media idempotency coverage is in place for CONTENT-01..CONTENT-06.
- Ready for `08-02-PLAN.md` wrapper infographic lifecycle tests (NLM-01..NLM-05).

---
*Phase: 08-content-wrapper-tests*
*Completed: 2026-02-23*

## Self-Check: PASSED

- FOUND: `.planning/phases/08-content-wrapper-tests/08-01-SUMMARY.md`
- FOUND: `5ca0698`
- FOUND: `57bfe32`
- FOUND: `a26eaa4`
