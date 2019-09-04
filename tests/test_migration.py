from unittest import TestCase

from piccolo.migrations.table import Migration


class TestMigrationTable(TestCase):
    def test_migration_table(self):
        Migration.create().run_sync()
        Migration.select().run_sync()
        Migration.drop().run_sync()
