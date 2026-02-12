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

Purpose: Enables the system to trigger deep research, poll for completion, generate synthesis, and handle API errors gracefully using notebooklm-py.

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
# Uses notebook_lm.py from Plan 01
# Uses database operations from Phase 1 for state transitions

# Key Technical Decisions
- Rate limiting: max_concurrent=3, min_interval=120 (2 min)
- Circuit breaker: failure_threshold=5, recovery_timeout=300 (5 min)
- Polling: every 60 seconds, 45 min timeout
</context>

<tasks>

<task type="auto">
  <name>Implement rate limiter</name>
  <files>src/article_factory/errors.py</files>
  <action>
    Create errors.py with:

    ```python
    import asyncio
    from typing import Optional
    from dataclasses import dataclass, field

    @dataclass
    class RateLimiter:
        """Rate limiter for NotebookLM API calls."""
        
        max_concurrent: int = 3
        min_interval: int = 120  # seconds
        
        _semaphore: asyncio.Semaphore = field(default_factory=asyncio.Semaphore)
        _last_call: float = 0.0
        _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
        
        def __post_init__(self):
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def acquire(self) -> bool:
            """Acquire permission to make API call."""
            await self._semaphore.acquire()
            async with self._lock:
                now = asyncio.get_event_loop().time()
                time_since_last = now - self._last_call
                if time_since_last < self.min_interval:
                    # Wait for minimum interval
                    await asyncio.sleep(self.min_interval - time_since_last)
                self._last_call = asyncio.get_event_loop().time()
            return True
        
        def release(self):
            """Release semaphore after API call."""
            self._semaphore.release()
    ```

    Usage:
    ```python
    rate_limiter = RateLimiter(max_concurrent=3, min_interval=120)
    
    async def make_api_call():
        await rate_limiter.acquire()
        try:
            # Your API call
            result = await client.notebooks.create(name)
            return result
        finally:
            rate_limiter.release()
    ```
  </action>
  <verify>
    Run `python -c "from article_factory.errors import RateLimiter; print('RateLimiter exists')"`
    Test: RateLimiter(max_concurrent=1) with 2 acquires should block
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

    ```python
    import asyncio
    from datetime import datetime
    from enum import Enum
    from typing import Optional, Callable
    from dataclasses import dataclass, field

    class CircuitState(Enum):
        CLOSED = "closed"      # Normal operation
        OPEN = "open"          # Blocking calls
        HALF_OPEN = "half_open"  # Testing recovery

    class CircuitOpenError(Exception):
        """Circuit breaker is open."""
        pass

    @dataclass
    class CircuitBreaker:
        """Circuit breaker for API failures."""
        
        failure_threshold: int = 5
        recovery_timeout: int = 300  # 5 minutes
        
        _state: CircuitState = CircuitState.CLOSED
        _failure_count: int = 0
        _last_failure: Optional[datetime] = None
        _recovery_task: Optional[asyncio.Task] = None
        
        @property
        def state(self) -> CircuitState:
            return self._state
        
        async def call(self, func: Callable, *args, **kwargs):
            """Execute function with circuit breaker protection."""
            if self._state == CircuitState.OPEN:
                raise CircuitOpenError("Circuit is open - too many failures")
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise
    
    # Add helper methods to CircuitBreaker class:
    async def _on_success(self):
        """Handle successful call."""
        self._failure_count = 0
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
    
    async def _on_failure(self):
        """Handle failed call."""
        self._failure_count += 1
        self._last_failure = datetime.now()
        
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            # Schedule recovery check
            self._recovery_task = asyncio.create_task(self._try_recover())
    
    async def _try_recover(self):
        """Try to close circuit after timeout."""
        await asyncio.sleep(self.recovery_timeout)
        self._state = CircuitState.HALF_OPEN
    ```

    Usage:
    ```python
    circuit = CircuitBreaker(failure_threshold=5, recovery_timeout=300)
    
    async def safe_api_call():
        return await circuit.call(client.notebooks.create, "name")
    ```
  </action>
  <verify>
    Run `python -c "from article_factory.errors import CircuitBreaker, CircuitOpenError; print('CircuitBreaker exists')"`
    Test: After 5 failures, should raise CircuitOpenError
  </verify>
  <done>
    Circuit breaker prevents cascade failures
  </done>
</task>

<task type="auto">
  <name>Implement research orchestration workflow</name>
  <files>src/article_factory/research.py</files>
  <action>
    Create research.py with:

    ```python
    import asyncio
    from datetime import datetime
    from typing import Optional
    
    from article_factory.notebook_lm import NotebookLMClientWrapper
    from article_factory.errors import RateLimiter, CircuitBreaker, CircuitOpenError
    from article_factory.database import (
        get_session, update_status, increment_retry,
        set_artifact_id, get_topic
    )

    # Global rate limiter and circuit breaker
    rate_limiter = RateLimiter(max_concurrent=3, min_interval=120)
    circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=300)

    async def start_research(topic_id: int):
        """Start research for a topic."""
        async with get_session() as session:
            topic = await get_topic(session, topic_id)
            
            if topic.status.value != "PENDING":
                raise ValueError(f"Topic {topic_id} is not PENDING")
            
            # Create notebook
            await rate_limiter.acquire()
            try:
                client = NotebookLMClientWrapper()
                notebook_id = await client.create_notebook_for_topic(topic_id, topic.topic, topic.prompt)
            finally:
                rate_limiter.release()
            
            # Trigger research
            await rate_limiter.acquire()
            try:
                await circuit_breaker.call(
                    client.start_research, notebook_id, topic.topic
                )
            finally:
                rate_limiter.release()
            
            # Update status
            await update_status(topic_id, "PROCESSING")
            
            return {"notebook_id": notebook_id, "status": "PROCESSING"}

    async def poll_research(topic_id: int, timeout: int = 2700):
        """Poll research completion."""
        client = NotebookLMClientWrapper()
        
        async with get_session() as session:
            topic = await get_topic(session, topic_id)
            notebook_id = topic.notebook_id
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Research timed out after {timeout}s")
            
            await rate_limiter.acquire()
            try:
                status = await circuit_breaker.call(
                    client.poll_research_status, notebook_id
                )
            finally:
                rate_limiter.release()
            
            if status["status"] == "completed":
                await update_status(topic_id, "COMPLETED")
                return {"status": "completed", "sources": status.get("sources", [])}
            
            elif status["status"] == "in_progress":
                await asyncio.sleep(60)  # Poll every 60 seconds
                continue
            
            else:
                await update_status(topic_id, "FAILED")
                await increment_retry(topic_id)
                raise RuntimeError(f"Research failed: {status}")

    async def run_research(topic_id: int):
        """Blocking call: start research and wait for completion."""
        try:
            result = await start_research(topic_id)
            result = await poll_research(topic_id)
            return result
        except Exception as e:
            await update_status(topic_id, "FAILED")
            await increment_retry(topic_id)
            raise
    ```

    State transitions:
    - NEW → PENDING (when enqueued)
    - PENDING → PROCESSING (when research starts)
    - PROCESSING → COMPLETED (on success)
    - PROCESSING → FAILED (on error, increments retry_count)
  </action>
  <verify>
    Run `python -c "from article_factory.research import start_research, poll_research, run_research; print('Research module loads')"`
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

    ```python
    import os
    from datetime import datetime
    
    async def generate_synthesis(notebook_id: str, topic_slug: str) -> str:
        """Generate research synthesis and save to file."""
        client = NotebookLMClientWrapper()
        
        # Generate using chat API
        await rate_limiter.acquire()
        try:
            result = await circuit_breaker.call(
                client.chat.ask, notebook_id,
                "Create a structured summary of all sources and key insights. Format as:\n\n## Key Findings\n- [bullet points]\n\n## Sources Summary\n- [list of sources]\n\n## Questions Answered\n- [Q&A format]\n\n## Knowledge Gaps\n- [areas for further research]"
            )
        finally:
            rate_limiter.release()
        
        # Save to output directory
        output_dir = f"output/{datetime.now().strftime('%Y-%m-%d')}/{topic_slug}"
        os.makedirs(output_dir, exist_ok=True)
        
        synthesis_path = f"{output_dir}/research_synthesis.md"
        with open(synthesis_path, "w") as f:
            f.write(f"# Research Synthesis\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write(result.answer)
        
        return synthesis_path
    ```

    Synthesis structure:
    - Key Findings (bullet points)
    - Sources Summary (list of sources)
    - Questions Answered (Q&A format)
    - Knowledge Gaps (areas for further research)
  </action>
  <verify>
    Run `python -c "from article_factory.research import generate_synthesis; print('Synthesis function exists')"`
  </verify>
  <done>
    Research synthesis generated and saved to structured output directory
  </done>
</task>

</tasks>

<verification>
1. Verify RateLimiter enforces concurrent/interval limits
2. Verify CircuitBreaker tracks failures and opens/closes correctly
3. Verify research workflow methods exist: start_research, poll_research, run_research
4. Verify generate_synthesis creates structured output
5. Verify error handling integration in research workflow
</verification>

<success_criteria>
- Research can be triggered and polled to completion
- Rate limiting prevents API key suspension (max 3 concurrent, 2 min interval)
- Circuit breaker handles cascading failures (5 failures = open)
- Research synthesis generated and persisted
- Error handling updates topic status correctly
</success_criteria>

<output>
After completion, create `.planning/phases/02-research-layer/02-research-SUMMARY.md`
</output>
