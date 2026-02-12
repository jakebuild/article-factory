---
phase: 02-research-layer
plan: "02"
type: execute
wave: 2
depends_on:
  - "01"
files_modified:
  - "src/article_factory/research.py"
  - "src/article_factory/errors.py"
autonomous: true
user_setup: []
---

<objective>
Implement research orchestration with async polling, synthesis generation, rate limiting, and circuit breaker.

Purpose: Enables the system to trigger deep research, poll for completion, generate synthesis, and handle API errors gracefully.

Output:
- Research workflow: trigger → poll → complete/synthesis
- Rate limiting (max 3 concurrent, 2-5 min poll interval)
- Circuit breaker for API failures
- Structured research synthesis output
</objective>

<execution_context>
@/Users/giangnguyen/.config/opencode/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/phases/02-research-layer/01-notebook-SUMMARY.md
# Requires Plan 01 completion (NotebookLM client, notebook operations)
# Uses database operations from Phase 1 for state transitions
# Uses notebook_lm.py from Plan 01
</context>

<tasks>

<task type="auto">
  <name>Implement research orchestration workflow</name>
  <files>src/article_factory/research.py</files>
  <action>
    Create research.py with:

    Research workflow:
    - start_research(topic_id: int): 
      1. Get topic from database
      2. Validate status is PENDING
      3. Create notebook name from topic
      4. Create notebook via notebook_lm.py
      5. Trigger deep research via notebook_lm.add_research()
      6. Update topic status to PROCESSING
      7. Return artifact_id for polling

    - poll_research(topic_id: int, artifact_id: str, timeout=2700):
      1. Poll artifact status every 60 seconds
      2. Handle timeout: raise TimeoutError after timeout seconds
      3. On complete: update topic status to COMPLETED
      4. Return artifact result

    - run_research(topic_id: int):
      1. Blocking call that runs start_research + poll_research
      2. Handles all errors, updates status to FAILED on error
      3. Increments retry_count on failure
  </action>
  <verify>
    Run `python -c "from article_factory.research import start_research, poll_research; print('Research module loads')" 2>&1`
    Verify method signatures exist
  </verify>
  <done>
    Research workflow provides blocking and non-blocking research execution
  </done>
</task>

<task type="auto">
  <name>Generate research synthesis</name>
  <files>src/article_factory/research.py</files>
  <action>
    Add to research.py:

    - generate_synthesis(notebook_id: str) -> str:
      1. Generate synthesis using NotebookLM text generation
      2. Prompt: "Create a structured summary of all sources and insights in this notebook"
      3. Return markdown-formatted synthesis
      4. Store synthesis in output directory: YYYY-MM-DD/topic-slug/research_synthesis.md

    Synthesis structure:
    - Key Findings (bullet points)
    - Sources Summary (list of imported sources)
    - Research Questions Answered (Q&A format)
    - Knowledge Gaps (areas requiring further research)
  </action>
  <verify>
    Run `python -c "from article_factory.research import generate_synthesis; print('Synthesis function exists')" 2>&1`
  </verify>
  <done>
    Research synthesis generated and saved to structured output directory
  </done>
</task>

<task type="auto">
  <name>Implement rate limiting</name>
  <files>src/article_factory/errors.py</files>
  <action>
    Create errors.py with:

    RateLimiter class:
    - __init__(max_concurrent=3, min_interval=120):
      - max_concurrent: Maximum concurrent API calls
      - min_interval: Minimum seconds between calls (2-5 min = 120-300s)

    - acquire() -> bool:
      - Returns True if call can proceed
      - Blocks and returns False if at limit
      - Tracks call timestamps in memory

    - record_call():
      - Records timestamp of successful call
      - Used for rate limit enforcement

    Usage:
    - Before each NotebookLM API call: rate_limiter.acquire()
    - After successful call: rate_limiter.record_call()
  </action>
  <verify>
    Run `python -c "from article_factory.errors import RateLimiter; print('RateLimiter class exists')" 2>&1`
  </verify>
  <done>
    Rate limiting prevents API key suspension
  </done>
</task>

<task type="auto">
  <name>Implement circuit breaker</name>
  <files>src/article_factory/errors.py</files>
  <action>
    Add to errors.py:

    CircuitBreaker class:
    - __init__(failure_threshold=5, recovery_timeout=300):
      - failure_threshold: Number of failures before opening circuit
      - recovery_timeout: Seconds before attempting recovery

    States: CLOSED, OPEN, HALF_OPEN

    - call(func, *args, **kwargs):
      - If OPEN: raise CircuitOpenError
      - If HALF_OPEN: allow single call, close on success
      - Execute function, track failures/successes
      - On failure: increment count, open if threshold reached

    Exceptions tracked:
      - API errors (not network errors)
      - Timeout errors (partial success)
      - Rate limit errors (don't count against circuit)

    Error types:
      - CircuitOpenError: Circuit is open, calls rejected
      - CircuitTooManyFailures: Permanent failure, manual reset needed
  </action>
  <verify>
    Run `python -c "from article_factory.errors import CircuitBreaker, CircuitOpenError; print('CircuitBreaker exists')" 2>&1`
  </verify>
  <done>
    Circuit breaker prevents cascade failures and provides clear error messages
  </done>
</task>

<task type="auto">
  <name>Integrate error handling into research workflow</name>
  <files>src/article_factory/research.py</files>
  <action>
    Update research.py to integrate RateLimiter and CircuitBreaker:

    - Global rate_limiter = RateLimiter(max_concurrent=3, min_interval=120)
    - Global circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=300)

    Research workflow with error handling:
    - start_research():
      - rate_limiter.acquire() before API calls
      - circuit_breaker.call() wrapping API calls
      - Record success/failure appropriately

    Error handling:
      - RateLimitError: Wait and retry (don't count as failure)
      - TimeoutError: Mark FAILED, increment retry_count
      - CircuitOpenError: Wait for recovery or manual intervention
      - APIError: Mark FAILED, increment retry_count
  </action>
  <verify>
    Run `python -c "from article_factory.research import run_research; print('Research with error handling loads')" 2>&1`
  </verify>
  <done>
    Research workflow includes rate limiting and circuit breaker protection
  </done>
</task>

</tasks>

<verification>
1. Verify research workflow methods exist: start_research, poll_research, run_research
2. Verify generate_synthesis creates structured output
3. Verify RateLimiter enforces concurrent/interval limits
4. Verify CircuitBreaker tracks failures and opens/closes correctly
5. Verify error handling integration in research workflow
</verification>

<success_criteria>
- Research can be triggered and polled to completion
- Rate limiting prevents API key suspension
- Circuit breaker handles cascading failures
- Research synthesis generated and persisted
- Error handling updates topic status correctly
</success_criteria>

<output>
After completion, create `.planning/phases/02-research-layer/02-research-SUMMARY.md`
</output>
