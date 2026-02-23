---
status: complete
phase: 08-content-wrapper-tests
source: 08-01-SUMMARY.md, 08-02-SUMMARY.md
started: 2026-02-23T04:16:33Z
updated: 2026-02-23T04:17:26Z
---

## Current Test

[testing complete]

## Tests

### 1. Content safety guard rejects disallowed prompts
expected: Running `.venv/bin/python -m pytest tests/test_article_generation.py -k "content_01 or safety" -v` passes and confirms `apply_safety_constraints` raises `ValueError` for disallowed patterns.
result: pass

### 2. Source citation validation rejects unknown citations
expected: Running `.venv/bin/python -m pytest tests/test_article_generation.py -k "content_02 or citation" -v` passes and confirms unknown citations raise `ValueError`.
result: pass

### 3. Article length validation rejects out-of-range content
expected: Running `.venv/bin/python -m pytest tests/test_article_generation.py -k "content_03 or length" -v` passes and confirms lengths outside bounds return `False`.
result: pass

### 4. Article generation defaults to report format
expected: Running `.venv/bin/python -m pytest tests/test_article_generation.py -k "content_04 or default" -v` passes and confirms report format is used when no format is provided.
result: pass

### 5. Output directory resolution supports dict and ORM-like topic shapes
expected: Running `.venv/bin/python -m pytest tests/test_media.py -k "content_05 or output_dir" -v` passes and confirms `get_output_dir` resolves both dict and object topic records.
result: pass

### 6. Media generation is idempotent when infographic file already exists
expected: Running `.venv/bin/python -m pytest tests/test_media.py -k "content_06 or idempotent" -v` passes and confirms existing infographic path is returned without re-triggering generation.
result: pass

### 7. Wrapper cleans FAILED artifacts and detects new artifact via diff
expected: Running `.venv/bin/python -m pytest tests/test_notebook_lm.py -k "nlm_01 or nlm_02 or cleanup or diff" -v` passes and confirms failed artifacts are removed and a newly created artifact is detected by before/after diff.
result: pass

### 8. Wrapper polling handles terminal COMPLETED and FAILED states correctly
expected: Running `.venv/bin/python -m pytest tests/test_notebook_lm.py -k "nlm_03 or nlm_04 or polling" -v` passes and confirms COMPLETED returns successfully while FAILED raises `RuntimeError`.
result: pass

### 9. Wrapper polling times out with explicit runtime error
expected: Running `.venv/bin/python -m pytest tests/test_notebook_lm.py -k "nlm_05 or timeout" -v` passes and confirms timeout path raises `RuntimeError` when completion is never reached.
result: pass

## Summary

total: 9
passed: 9
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
