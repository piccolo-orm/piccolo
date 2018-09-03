import asyncio
from unittest import TestCase

import asyncpg

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
            return await query.execute()

        async def get_pokemon():
            return await Pokemon.select().execute()

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
            return await query.execute()

        async def get_pokemon():
            return await Pokemon.select().execute()

        asyncio.run(drop_column())

        response = asyncio.run(get_pokemon())

        column_names = response[0].keys()
        self.assertTrue(
            'power' not in column_names
        )
