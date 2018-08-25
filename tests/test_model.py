# Need a test runner ...
import asyncio
from unittest import TestCase

import asyncpg

from aragorm.model import Model


TEST_CREDENTIALS = {
    'host': 'localhost',
    'database': 'aragorm',
    'user': 'aragorm',
    'password': 'aragorm'
}


class Pokemon(Model):
    pass


class TestQuery(TestCase):

    async def create_table(self):
        conn = await asyncpg.connect(**TEST_CREDENTIALS)
        await conn.execute('''
            CREATE TABLE pokemon (
                name VARCHAR(50),
                power SMALLINT
            );'''
        )
        await conn.close()

    async def insert_rows(self):
        conn = await asyncpg.connect(**TEST_CREDENTIALS)
        await conn.execute('''
            INSERT INTO pokemon (
                name,
                power
            ) VALUES (
                'pikachu',
                1000
            );'''
        )

    async def drop_table(self):
        conn = await asyncpg.connect(**TEST_CREDENTIALS)
        await conn.execute('DROP TABLE pokemon;')
        await conn.close()

    def setUp(self):
        asyncio.run(self.create_table())

    async def get_pokemon(self):
        return await Pokemon.select().execute()

    def test_query(self):
        asyncio.run(self.insert_rows())
        response = asyncio.run(self.get_pokemon())
        print(f'response = {response}')
        # breakpoint()

    def tearDown(self):
        asyncio.run(self.drop_table())
