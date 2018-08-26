# Need a test runner ...
import asyncio
from unittest import TestCase

import asyncpg

from example_project.models import Pokemon


TEST_CREDENTIALS = {
    'host': 'localhost',
    'database': 'aragorm',
    'user': 'aragorm',
    'password': 'aragorm'
}


class DBTestCase(TestCase):

    def execute(self, query):
        async def _execute():
            connection = await asyncpg.connect(**TEST_CREDENTIALS)
            await connection.execute(query)
            await connection.close()

        asyncio.run(_execute())


class TestQuery(DBTestCase):

    def create_table(self):
        self.execute('''
            CREATE TABLE pokemon (
                name VARCHAR(50),
                power SMALLINT
            );'''
        )

    def insert_rows(self):
        self.execute('''
            INSERT INTO pokemon (
                name,
                power
            ) VALUES (
                'pikachu',
                1000
            );'''
        )

    def drop_table(self):
        self.execute('DROP TABLE pokemon;')

    def setUp(self):
        self.create_table()

    def test_query_all_columns(self):
        self.insert_rows()

        async def get_pokemon():
            return await Pokemon.select().execute()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertDictEqual(
            response,
            {'name': 'pikachu', 'power': 1000}
        )

    def test_query_some_columns(self):
        self.insert_rows()

        async def get_pokemon():
            return await Pokemon.select('name').execute()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertDictEqual(
            response,
            {'name': 'pikachu'}
        )

    def tearDown(self):
        self.drop_table()
