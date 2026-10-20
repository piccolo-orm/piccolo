from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, TypeVar

ReturnType = TypeVar("ReturnType")


def run_sync(
    coroutine: Coroutine[Any, Any, ReturnType],
) -> ReturnType:
    """
    Run the coroutine synchronously - trying to accommodate as many edge cases
    as possible.
     1. When called within a coroutine.
     2. When called from ``python -m asyncio``, or iPython with %autoawait
        enabled, which means an event loop may already be running in the
        current thread.
    """
    try:
        # We try this first, as in most situations this will work.
        return asyncio.run(coroutine)
    except RuntimeError:
        # An event loop already exists.
        with ThreadPoolExecutor(max_workers=1) as executor:
            future: Future = executor.submit(asyncio.run, coroutine)
            return future.result()
