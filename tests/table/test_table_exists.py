import asyncio
from unittest import TestCase

from ..example_project.tables import Pokemon


class TestTableExists(TestCase):

    def setUp(self):
        asyncio.run(Pokemon.create().execute())

    def test_table_exists(self):
        response = asyncio.run(Pokemon.table_exists().execute())
        self.assertTrue(response[0]['exists'] is True)

    def tearDown(self):
        asyncio.run(Pokemon.drop().execute())
