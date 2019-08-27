import asyncio

from unittest import TestCase

from ..base import DBTestCase
from ..example_project.tables import Manager


class TestPool(DBTestCase):
    async def create_pool(self):
        await Manager.Meta.db.start_connnection_pool()
        await Manager.Meta.db.close_connnection_pool()

    async def make_queries(self):
        await Manager.Meta.db.start_connnection_pool()

        await Manager(name="Bob").save().run()
        response = await Manager.select().run()
        self.assertTrue("Bob" in [i["name"] for i in response])

        await Manager.Meta.db.close_connnection_pool()

    def test_creation(self):
        """
        Make sure a connection pool can be created.
        """
        asyncio.run(self.create_pool())

    def test_queries(self):
        """
        Make several queries using a connection pool.
        """
        asyncio.run(self.make_queries())
