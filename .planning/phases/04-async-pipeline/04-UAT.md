---
status: complete
phase: 04-async-pipeline
source: 04-scheduler-SUMMARY.md, 04-progress-SUMMARY.md, 04-status-SUMMARY.md, 04-async-pipeline-04-SUMMARY.md, 04-async-pipeline-05-SUMMARY.md
started: 2026-02-12T12:00:00Z
updated: 2026-02-12T17:45:00Z
---

## Current Test

[testing complete]

Found 4 issues requiring fixes:
1. Scheduler daemon threads die before completion
2. Sources not discovered/imported
3. Chat API returns empty (no sources)
4. Report generation fails (no sources)

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
issues: 4
pending: 0
skipped: 2
untested: 0

## Gaps

- truth: "Live pipeline runs to completion: notebook creation → research → synthesis → article → media"
  status: failed
  reason: "Tasks created but scheduler daemon threads die. Research status shows 'in progress' but never completes."
  severity: major
  test: 7
- truth: "Source discovery and import works"
  status: failed  
  reason: "Research completes but sources not found in notebook. Notebook has no sources."
  severity: major
  test: 8
- truth: "Article generation via chat API works with sources"
  status: failed
  reason: "Chat API returns empty - notebook has no sources to reference."
  severity: major
  test: 9
- truth: "Report generation works"
  status: failed
  reason: "Report generation failed - notebook has no sources. 'GenerationStatus.task_id' empty."
  severity: major
  test: 11

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

### 7. Live pipeline execution
expected: Full pipeline runs: notebook creation → research → synthesis → article → media
result: issue
reported: "Tasks created but scheduler daemon threads die. Pipeline never progresses past PENDING."
severity: major

### 8. Source discovery and import
expected: Deep research finds sources and auto-imports them
result: issue
reported: "Research status incomplete. Notebook has no sources despite research being triggered."
severity: major

### 9. Article generation from synthesis
expected: Article generated from notebook sources using chat API
result: issue
reported: "Chat API returns empty - no sources in notebook to reference."
severity: major

### 10. Article length validation
expected: Generated article meets 2000-2500 word requirement
result: issue
reported: "Cannot validate - no articles generated due to empty notebook."
severity: major
