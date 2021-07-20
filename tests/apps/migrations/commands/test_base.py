import os
from unittest import TestCase
from unittest.mock import MagicMock, patch

from piccolo.apps.migrations.commands.base import (
    BaseMigrationManager,
    Migration,
)
from piccolo.conf.apps import AppConfig
from piccolo.utils.sync import run_sync


class TestBaseMigrationManager(TestCase):
    def test_create_migration_table(self):
        self.assertTrue(
            run_sync(BaseMigrationManager().create_migration_table())
        )

    def tearDown(self):
        Migration.raw("DROP TABLE IF EXISTS migration").run_sync()


class TestGetMigrationModules(TestCase):
    def test_get_migration_modules(self):
        app_config = AppConfig(
            app_name="music",
            migrations_folder_path=os.path.join(
                os.path.dirname(__file__), "test_migrations"
            ),
        )

        migration_managers = run_sync(
            BaseMigrationManager().get_migration_managers(
                app_config=app_config
            )
        )

        self.assertTrue(len(migration_managers) == 1)
        self.assertTrue(
            migration_managers[0].migration_id == "2020-03-31T20:38:22"
        )


class TestGetTableFromSnapshot(TestCase):
    @patch.object(BaseMigrationManager, "get_app_config")
    def test_get_table_from_snaphot(self, get_app_config: MagicMock):
        """
        Test the get_table_from_snaphot method.
        """
        get_app_config.return_value = AppConfig(
            app_name="music",
            migrations_folder_path=os.path.join(
                os.path.dirname(__file__), "test_migrations"
            ),
        )

        table = run_sync(
            BaseMigrationManager().get_table_from_snaphot(
                app_name="music", table_class_name="Band"
            )
        )
        self.assertTrue(table.class_name == "Band")
