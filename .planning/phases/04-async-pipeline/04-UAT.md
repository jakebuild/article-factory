---
status: testing
phase: 04-async-pipeline
source: 04-scheduler-SUMMARY.md, 04-progress-SUMMARY.md, 04-status-SUMMARY.md, 04-async-pipeline-04-SUMMARY.md, 04-async-pipeline-05-SUMMARY.md
started: 2026-02-12T12:00:00Z
updated: 2026-02-12T17:30:00Z
---

## Current Test

number: 11
name: Report Format CLI Option
expected: |
  Running `article-factory article <topic-id> --format report --prompt "..."` generates an article using the report artifact API instead of synthesis fallback.
awaiting: user response

## Tests

### 1-10. [Previous tests from original Phase 4 UAT - see below]

### 11. Report Format CLI Option
expected: Running `article-factory article <topic-id> --format report --prompt "..."` generates an article using the report artifact API instead of synthesis fallback.
result: pass

### 12. Synthesis Format CLI Option  
expected: Running `article-factory article <topic-id> --format synthesis --prompt "..."` generates an article using the synthesis fallback (original behavior).
result: pass

### 13. generate_article() Function
expected: The `generate_article()` function in article.py accepts a `format` parameter ("synthesis" or "report") and routes to the appropriate generation method.
result: pass

## Summary

total: 13
passed: 7
issues: 0
pending: 0
skipped: 2
untested: 4 (requires API credentials)

## Gaps

[none]

---

## Previous Tests (from original Phase 4 testing)

### 1. Non-blocking run command
expected: Running `article-factory run <topic-id>` returns a task_id immediately without waiting for the pipeline to complete.
result: pass

### 2. Status command shows task details
expected: Running `article-factory status <task-id>` shows task_id, topic_id, current stage, and progress percentage.
result: pass

### 3. Cancel command works
expected: Running `article-factory cancel <task-id>` on a pending or running task cancels it and confirms cancellation.
result: pass

### 4. Progress bar displays during execution
expected: During pipeline execution, a progress bar like `[████████░░] XX%` updates to show current stage and completion percentage.
result: skipped
reason: Requires NotebookLM API credentials to actually run pipeline

### 5. Completion notification
expected: When the pipeline finishes, a notification shows with output location.
result: skipped
reason: Requires NotebookLM API credentials to actually run pipeline

### 6. Configurable output directory
expected: Running `article-factory run <topic-id> --output-dir /custom/path` stores results in the specified directory.
result: pass

### 7. Live pipeline execution (2026-02-14)
expected: Full pipeline runs: notebook creation → research → synthesis → article → media
result: untested
reason: Requires NotebookLM API credentials

### 8. Source discovery and import
expected: Deep research finds sources and auto-imports them
result: untested
reason: Requires NotebookLM API credentials

### 9. Article generation from synthesis (2026-02-14)
expected: Article generated from notebook sources using chat API
result: untested
reason: Requires NotebookLM API credentials

### 10. Article length validation (2026-02-14)
expected: Generated article meets 2000-2500 word requirement
result: untested
reason: Requires NotebookLM API credentials
