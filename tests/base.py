import asyncio
from unittest import TestCase

import asyncpg

from .example_project.tables import Band


class DBTestCase(TestCase):

    def run_sync(self, query):
        async def _run():
            connection = await asyncpg.connect(**Band.Meta.db.config)
            await connection.execute(query)
            await connection.close()

        asyncio.run(_run())

    def create_table(self):
        self.run_sync('''
            CREATE TABLE band (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50),
                manager VARCHAR(20),
                popularity SMALLINT
            );''')

    def insert_row(self):
        self.run_sync('''
            INSERT INTO band (
                name,
                manager,
                popularity
            ) VALUES (
                'Pythonistas',
                'ash',
                1000
            );''')

    def insert_rows(self):
        self.run_sync('''
            INSERT INTO band (
                name,
                manager,
                popularity
            ) VALUES (
                'Pythonistas',
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
            );''')

    def drop_table(self):
        self.run_sync('DROP TABLE band;')

    def setUp(self):
        self.create_table()

    def tearDown(self):
        self.drop_table()
