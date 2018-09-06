import asyncio

from ..base import DBTestCase
from ..example_project.tables import Pokemon


class TestSelect(DBTestCase):

    def test_query_all_columns(self):
        self.insert_row()

        async def get_pokemon():
            return await Pokemon.select().run()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertDictEqual(
            response[0],
            {'name': 'pikachu', 'trainer': 'ash', 'power': 1000}
        )

    def test_query_some_columns(self):
        self.insert_row()

        async def get_pokemon():
            return await Pokemon.select('name').run()

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
            ).run()

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
            ).run()

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
            ).run()

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
            ).run()

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
            ).run()

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
            ).run()

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
            ).run()

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
            return await query.run()

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
            ).run()

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
            ).run()

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
            ).limit(1).run()

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
            ).limit(1).run()

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
            ).count().run()

        response = asyncio.run(get_pokemon())
        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'count': 1}]
        )
