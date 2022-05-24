from __future__ import annotations

import asyncio
import typing as t
from concurrent.futures import ThreadPoolExecutor


def run_sync(coroutine: t.Coroutine):
    """
    Run the coroutine synchronously - trying to accommodate as many edge cases
    as possible.
     1. When called within a coroutine.
     2. When called from ``python -m asyncio``, or iPython with %autoawait
        enabled, which means an event loop may already be running in the
        current thread.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No current event loop, so it's safe to use:
        return asyncio.run(coroutine)
    else:
        # We're already inside a running event loop, so run the coroutine in a
        # new thread:
        new_loop = asyncio.new_event_loop()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(new_loop.run_until_complete, coroutine)
            return future.result()
