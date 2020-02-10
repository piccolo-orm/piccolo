import asyncio

from ..base import DBTestCase, postgres_only
from ..example_project.tables import Manager


@postgres_only
class TestPool(DBTestCase):
    async def _create_pool(self):
        await Manager._meta.db.start_connnection_pool()
        await Manager._meta.db.close_connnection_pool()

    async def _make_query(self):
        await Manager._meta.db.start_connnection_pool()

        await Manager(name="Bob").save().run()
        response = await Manager.select().run()
        self.assertTrue("Bob" in [i["name"] for i in response])

        await Manager._meta.db.close_connnection_pool()

    async def _make_many_queries(self):
        await Manager._meta.db.start_connnection_pool()

        await Manager(name="Bob").save().run()

        async def get_data():
            response = await Manager.select().run()
            self.assertEqual(response, [{"id": 1, "name": "Bob"}])

        await asyncio.gather(*[get_data() for _ in range(500)])

        await Manager._meta.db.close_connnection_pool()

    def test_creation(self):
        """
        Make sure a connection pool can be created.
        """
        asyncio.run(self._create_pool())

    def test_query(self):
        """
        Make several queries using a connection pool.
        """
        asyncio.run(self._make_query())

    def test_many_queries(self):
        """
        Make sure the connection pool is working correctly, and we don't
        exceed a connection limit - queries should queue, then succeed.
        """
        asyncio.run(self._make_many_queries())
