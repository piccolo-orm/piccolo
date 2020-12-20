import os
import shutil
from unittest import TestCase

from piccolo.conf.apps import AppConfig
from piccolo.apps.migrations.commands.new import (
    _create_new_migration,
    BaseMigrationManager,
    new,
)
from piccolo.utils.sync import run_sync

from tests.base import postgres_only
from tests.example_app.tables import Manager


class TestNewMigrationCommand(TestCase):
    def test_create_new_migration(self):
        """
        Create a manual migration (i.e. non-auto).
        """
        migration_folder = "/tmp/piccolo_migrations/"

        if os.path.exists(migration_folder):
            shutil.rmtree(migration_folder)

        os.mkdir(migration_folder)

        app_config = AppConfig(
            app_name="music",
            migrations_folder_path=migration_folder,
            table_classes=[Manager],
        )

        run_sync(_create_new_migration(app_config, auto=False))

        migration_modules = BaseMigrationManager().get_migration_modules(
            migration_folder
        )

        self.assertTrue(len(migration_modules.keys()) == 1)

    @postgres_only
    def test_new_command(self):
        """
        Call the command, when no migration changes are needed.
        """
        with self.assertRaises(SystemExit) as manager:
            run_sync(new(app_name="example_app", auto=True))

        self.assertEqual(
            manager.exception.__str__(), "No changes detected - exiting."
        )
