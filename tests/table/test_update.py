import asyncio

import asyncpg

from ..base import DBTestCase
from ..example_project.tables import Pokemon


class TestUpdate(DBTestCase):

    def test_update(self):
        self.insert_rows()

        async def update_pokemon():
            return await Pokemon.update(
                name='kakuna'
            ).where(
                Pokemon.name == 'weedle'
            ).execute()

        async def check_pokemon():
            return await Pokemon.select(
                'name'
            ).where(
                Pokemon.name == 'kakuna'
            ).execute()

        asyncio.run(update_pokemon())
        response = asyncio.run(check_pokemon())
        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'kakuna'}]
        )
