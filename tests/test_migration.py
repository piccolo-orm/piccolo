from unittest import TestCase

from piccolo.migrations.table import Migration


class TestMigrationTable(TestCase):
    def test_migration_table(self):
        Migration.create_table().run_sync()
        Migration.select().run_sync()
        Migration.alter().drop_table().run_sync()
