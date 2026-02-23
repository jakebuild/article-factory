"""Resilience tests for rate limiter and circuit breaker primitives."""

import asyncio

import pytest

from article_factory.errors import CircuitBreaker, CircuitOpenError, CircuitState, RateLimiter


@pytest.mark.asyncio
async def test_err_01_rate_limiter_blocks_fourth_concurrent_caller():
    limiter = RateLimiter(max_concurrent=3, min_interval=0)
    release_event = asyncio.Event()
    acquired_events = [asyncio.Event() for _ in range(3)]

    async def holding_worker(acquired_event: asyncio.Event) -> None:
        await limiter.acquire()
        acquired_event.set()
        await release_event.wait()
        limiter.release()

    workers = [
        asyncio.create_task(holding_worker(acquired_event))
        for acquired_event in acquired_events
    ]

    await asyncio.gather(
        *(asyncio.wait_for(acquired_event.wait(), timeout=0.2) for acquired_event in acquired_events)
    )

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(limiter.acquire(), timeout=0.05)

    release_event.set()
    await asyncio.gather(*workers)

    await asyncio.wait_for(limiter.acquire(), timeout=0.2)
    limiter.release()


@pytest.mark.asyncio
async def test_err_02_circuit_breaker_opens_and_rejects_calls():
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0)

    async def fail_call() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await breaker.call(fail_call)
    with pytest.raises(RuntimeError):
        await breaker.call(fail_call)

    assert breaker.state == CircuitState.OPEN

    with pytest.raises(CircuitOpenError):
        await breaker.call(fail_call)

    assert breaker._failure_count == 2


@pytest.mark.asyncio
async def test_err_03_circuit_breaker_recovers_after_cooldown():
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0)

    async def fail_call() -> None:
        raise RuntimeError("boom")

    async def successful_call() -> str:
        return "ok"

    with pytest.raises(RuntimeError):
        await breaker.call(fail_call)
    with pytest.raises(RuntimeError):
        await breaker.call(fail_call)

    assert breaker.state == CircuitState.OPEN

    async def wait_for_half_open() -> None:
        while breaker.state != CircuitState.HALF_OPEN:
            await asyncio.sleep(0.005)

    await asyncio.wait_for(wait_for_half_open(), timeout=0.2)
    assert breaker.state == CircuitState.HALF_OPEN

    result = await breaker.call(successful_call)

    assert result == "ok"
    assert breaker.state == CircuitState.CLOSED
    assert breaker._failure_count == 0
