import asyncio
from unittest import TestCase

import asyncpg

from .example_project.tables import Pokemon


class DBTestCase(TestCase):

    def execute(self, query):
        async def _execute():
            connection = await asyncpg.connect(**Pokemon.Meta.db)
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
