import asyncio
from unittest import TestCase

import asyncpg
from aragorm.migrations.table import Migration

from .example_project.tables import DB


class MigrationTest(Migration):

    class Meta():
        tablename = 'migration'
        db = DB


class TestMigrationTable(TestCase):

    def test_migration_table(self):
        async def create_table():
            return await MigrationTest.create().run()

        async def query_table():
            return await MigrationTest.select().run()

        async def drop_table():
            return await MigrationTest.drop().run()

        asyncio.run(create_table())
        asyncio.run(query_table())
        asyncio.run(drop_table())
