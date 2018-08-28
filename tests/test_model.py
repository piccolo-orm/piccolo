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

    def create_table(self):
        self.execute('''
            CREATE TABLE pokemon (
                name VARCHAR(50),
                trainer VARCHAR(20),
                power SMALLINT
            );'''
        )

    def insert_row(self):
        self.execute('''
            INSERT INTO pokemon (
                name,
                trainer,
                power
            ) VALUES (
                'pikachu',
                'ash',
                1000
            );'''
        )

    def insert_rows(self):
        self.execute('''
            INSERT INTO pokemon (
                name,
                trainer,
                power
            ) VALUES (
                'pikachu',
                'ash',
                1000
            ),(
                'raichu',
                'sally',
                2000
            ),(
                'weedle',
                'gordon',
                10
            );'''
        )

    def drop_table(self):
        self.execute('DROP TABLE pokemon;')

    def setUp(self):
        self.create_table()

    def tearDown(self):
        self.drop_table()


class TestSelect(DBTestCase):

    def test_query_all_columns(self):
        self.insert_row()

        async def get_pokemon():
            return await Pokemon.select().execute()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertDictEqual(
            response[0],
            {'name': 'pikachu', 'trainer': 'ash', 'power': 1000}
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

    def test_multiple_where(self):
        """
        Test that chaining multiple where clauses works results in an AND.
        """
        self.insert_rows()

        query = Pokemon.select(
            'name'
        ).where(
            Pokemon.name == 'raichu'
        ).where(
            Pokemon.trainer == 'sally'
        )

        async def get_pokemon():
            return await query.execute()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'raichu'}]
        )
        self.assertTrue(
            'AND' in query.__str__()
        )

    def test_complex_where(self):
        """
        Test a complex where clause - combining AND, and OR.
        """
        self.insert_rows()

        async def get_pokemon():
            return await Pokemon.select(
                'name'
            ).where(
                ((Pokemon.power == 2000) & (Pokemon.trainer == 'sally')) |
                ((Pokemon.power == 10) & (Pokemon.trainer == 'gordon'))
            ).execute()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'raichu'}, {'name': 'weedle'}]
        )

    def test_limit(self):
        self.insert_rows()

        async def get_pokemon():
            return await Pokemon.select(
                'name'
            ).limit(
                1
            ).execute()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'pikachu'}]
        )

    def test_order_by_ascending(self):
        self.insert_rows()

        async def get_pokemon():
            return await Pokemon.select(
                'name'
            ).order_by(
                'name'
            ).limit(1).execute()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'pikachu'}]
        )

    def test_order_by_decending(self):
        self.insert_rows()

        async def get_pokemon():
            return await Pokemon.select(
                'name'
            ).order_by(
                '-name'
            ).limit(1).execute()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'weedle'}]
        )

    def test_count(self):
        self.insert_rows()

        async def get_pokemon():
            return await Pokemon.select().where(
                Pokemon.name == 'pikachu'
            ).count().execute()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'count': 1}]
        )


class TestUpdate(DBTestCase):

    def test_update(self):
        self.insert_rows()

        async def update_pokemon():
            return await Pokemon.update(
                name='kakuna'
            ).execute()

        async def check_pokemon():
            return await Pokemon.select().where(Pokemon.name == 'kakuna')

        asyncio.run(update_pokemon())
        response = asyncio.run(update_pokemon())
        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'kakuna'}]
        )


class TestMetaClass(TestCase):

    def test_tablename(self):
        self.assertEqual(Pokemon.tablename, 'pokemon')
