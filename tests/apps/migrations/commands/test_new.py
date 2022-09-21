import os
import shutil
import tempfile
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from piccolo.apps.migrations.commands.new import (
    BaseMigrationManager,
    _create_new_migration,
    new,
)
from piccolo.conf.apps import AppConfig
from piccolo.utils.sync import run_sync
from tests.base import postgres_only
from tests.example_apps.music.tables import Manager


class TestNewMigrationCommand(TestCase):
    def test_create_new_migration(self):
        """
        Create a manual migration (i.e. non-auto).
        """
        migration_folder = os.path.join(
            tempfile.gettempdir(), "piccolo_migrations"
        )
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
    @patch("piccolo.apps.migrations.commands.new.print")
    def test_new_command(self, print_: MagicMock):
        """
        Call the command, when no migration changes are needed.
        """
        with self.assertRaises(SystemExit) as manager:
            run_sync(new(app_name="music", auto=True))

        self.assertEqual(manager.exception.code, 0)

        self.assertTrue(
            print_.mock_calls[-1] == call("No changes detected - exiting.")
        )
