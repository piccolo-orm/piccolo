import asyncio


def run_sync(coroutine):
    return asyncio.run(coroutine)
