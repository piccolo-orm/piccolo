import asyncio

from ..base import DBTestCase
from ..example_project.tables import Pokemon


class TestDelete(DBTestCase):

    def test_delete(self):
        self.insert_rows()

        async def delete_pokemon():
            return await Pokemon.delete().where(
                Pokemon.name == 'weedle'
            ).run()

        async def check_pokemon():
            return await Pokemon.select().where(
                Pokemon.name == 'weedle'
            ).count().run()

        asyncio.run(delete_pokemon())
        response = asyncio.run(check_pokemon())
        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'count': 0}]
        )
