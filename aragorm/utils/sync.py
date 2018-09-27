import asyncio


def run_sync(coroutine):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

    return loop.run_until_complete(coroutine)
