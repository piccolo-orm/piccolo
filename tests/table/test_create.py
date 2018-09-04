import asyncio

from ..base import DBTestCase
from ..example_project.tables import Pokemon


class TestCreate(DBTestCase):

    def setUp(self):
        """
        Need to override, otherwise table will be auto created.
        """
        pass

    def test_create_table(self):
        async def create_table():
            return await Pokemon.create().execute()

        async def count_rows():
            return await Pokemon.select(
                'name', 'trainer', 'power'
            ).count().execute()

        asyncio.run(create_table())

        # Just do a count to make sure the table was created ok.
        response = asyncio.run(count_rows())
        self.assertEqual(response[0]['count'], 0)
