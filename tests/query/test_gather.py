import asyncio

from tests.base import DBTestCase
from tests.example_apps.music.tables import Manager


class TestAwait(DBTestCase):
    def test_await(self):
        """
        Make sure that asyncio.gather works with the main query types.
        """

        async def run_queries():
            return await asyncio.gather(
                Manager.select(),
                Manager.insert(Manager(name="Golangs")),
                Manager.delete().where(Manager.name != "Golangs"),
                Manager.objects(),
                Manager.count(),
                Manager.raw("SELECT * FROM manager"),
            )

        # No exceptions should be raised.
        self.assertIsInstance(asyncio.run(run_queries()), list)
