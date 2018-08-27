import asyncio
from unittest import TestCase

import asyncpg

from .example_project.models import Pokemon


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

    def insert_row(self):
        self.execute('''
            INSERT INTO pokemon (
                name,
                power
            ) VALUES (
                'pikachu',
                1000
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
            ),(
                'raichu',
                2000
            ),(
                'weedle',
                10
            );'''
        )

    def drop_table(self):
        self.execute('DROP TABLE pokemon;')

    def setUp(self):
        self.create_table()

    def test_query_all_columns(self):
        self.insert_row()

        async def get_pokemon():
            return await Pokemon.select().execute()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertDictEqual(
            response[0],
            {'name': 'pikachu', 'power': 1000}
        )

    def test_query_some_columns(self):
        self.insert_row()

        async def get_pokemon():
            return await Pokemon.select('name').execute()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertDictEqual(
            response[0],
            {'name': 'pikachu'}
        )

    def test_where_like(self):
        self.insert_rows()

        async def get_pokemon():
            return await Pokemon.select(
                'name'
            ).where(
                Pokemon.name.like('%chu')
            ).execute()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'pikachu'}, {'name': 'raichu'}]
        )

    def test_where_greater_than(self):
        self.insert_rows()

        async def get_pokemon():
            return await Pokemon.select(
                'name'
            ).where(
                Pokemon.power > 1000
            ).execute()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'raichu'}]
        )

    def test_where_greater_equal_than(self):
        self.insert_rows()

        async def get_pokemon():
            return await Pokemon.select(
                'name'
            ).where(
                Pokemon.power >= 1000
            ).execute()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'pikachu'}, {'name': 'raichu'}]
        )

    def test_where_less_than(self):
        self.insert_rows()

        async def get_pokemon():
            return await Pokemon.select(
                'name'
            ).where(
                Pokemon.power < 1000
            ).execute()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'weedle'}]
        )

    def test_where_less_equal_than(self):
        self.insert_rows()

        async def get_pokemon():
            return await Pokemon.select(
                'name'
            ).where(
                Pokemon.power <= 1000
            ).execute()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'pikachu'}, {'name': 'weedle'}]
        )

    def test_where_and(self):
        self.insert_rows()

        async def get_pokemon():
            return await Pokemon.select(
                'name'
            ).where(
                (Pokemon.power <= 1000) & (Pokemon.name.like('%chu'))
            ).execute()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'pikachu'}]
        )

    def test_where_or(self):
        self.insert_rows()

        async def get_pokemon():
            return await Pokemon.select(
                'name'
            ).where(
                (Pokemon.name == 'raichu') | (Pokemon.name == 'weedle')
            ).execute()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'raichu'}, {'name': 'weedle'}]
        )

    def tearDown(self):
        self.drop_table()


class TestMetaClass(TestCase):

    def test_tablename(self):
        self.assertEqual(Pokemon.tablename, 'pokemon')
