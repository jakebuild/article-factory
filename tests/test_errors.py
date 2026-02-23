"""Resilience tests for rate limiter and circuit breaker primitives."""

import asyncio

import pytest

from article_factory.errors import RateLimiter


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
