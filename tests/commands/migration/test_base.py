from unittest import TestCase

from piccolo.commands.migration.base import BaseMigrationManager, Migration


class TestBaseMigrationManager(TestCase):
    def test_create_migration_table(self):
        self.assertTrue(BaseMigrationManager().create_migration_table())

    def tearDown(self):
        Migration.raw("DROP TABLE IF EXISTS migration").run_sync()
