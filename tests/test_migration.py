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
        MigrationTest.create().run_sync()
        MigrationTest.select().run_sync()
        MigrationTest.drop().run_sync()
