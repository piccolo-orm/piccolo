import asyncio
from unittest import TestCase

import asyncpg
from aragorm.columns import Integer

from .base import DBTestCase
from .example_project.tables import Pokemon


class TestRename(DBTestCase):

    def test_rename(self):
        self.insert_row()

        async def rename_row():
            query = Pokemon.alter().rename(
                Pokemon.power,
                'rating'
            )
            print(query)
            return await query.run()

        async def get_pokemon():
            return await Pokemon.select().run()

        asyncio.run(rename_row())

        response = asyncio.run(get_pokemon())

        column_names = response[0].keys()
        self.assertTrue(
            ('rating' in column_names) and ('power' not in column_names)
        )


class TestDrop(DBTestCase):

    def test_drop(self):
        self.insert_row()

        async def drop_column():
            query = Pokemon.alter().drop(
                Pokemon.power,
            )
            print(query)
            return await query.run()

        async def get_pokemon():
            return await Pokemon.select().run()

        asyncio.run(drop_column())

        response = asyncio.run(get_pokemon())

        column_names = response[0].keys()
        self.assertTrue(
            'power' not in column_names
        )


class TestAdd(DBTestCase):

    def test_add(self):
        """
        This needs a lot more work. Need to set values for existing rows.

        Just write the test for now ...
        """
        self.insert_row()

        async def add_column():
            query = Pokemon.alter().add(
                'weight',
                Integer(),
            )
            print(query)
            return await query.run()

        async def get_pokemon():
            return await Pokemon.select().run()

        asyncio.run(add_column())

        response = asyncio.run(get_pokemon())

        column_names = response[0].keys()
        self.assertTrue('weight' in column_names)

        self.assertEqual(response[0]['weight'], None)


class TestMultiple(DBTestCase):
    pass
