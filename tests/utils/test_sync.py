import asyncio
from unittest import TestCase

from piccolo.utils.sync import run_sync


class TestSync(TestCase):
    def test_sync_simple(self):
        """
        Test calling a simple coroutine.
        """
        run_sync(asyncio.sleep(0.1))

    def test_sync_nested(self):
        """
        Test calling a coroutine, which contains a call to `run_sync`.
        """

        async def test():
            run_sync(asyncio.sleep(0.1))

        run_sync(test())

    def test_sync_stopped_event_loop(self):
        """
        Test calling a coroutine, when the current thread has an event loop,
        but it isn't running.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        run_sync(asyncio.sleep(0.1))

        asyncio.set_event_loop(None)
