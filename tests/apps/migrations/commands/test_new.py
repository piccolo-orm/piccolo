import datetime
import os
import shutil
import tempfile
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from piccolo.apps.migrations.commands.new import (
    BaseMigrationManager,
    _create_new_migration,
    _generate_migration_meta,
    new,
)
from piccolo.conf.apps import AppConfig
from piccolo.utils.sync import run_sync
from tests.base import engines_only
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

    @engines_only("postgres")
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


class TestGenerateMigrationMeta(TestCase):
    @patch("piccolo.apps.migrations.commands.new.now")
    def test_filename(self, now: MagicMock):
        now.return_value = datetime.datetime(
            year=2022,
            month=1,
            day=10,
            hour=7,
            minute=15,
            second=20,
            microsecond=3000,
        )

        # Try with an app name which already contains valid characters for a
        # Python module.
        migration_meta = _generate_migration_meta(
            app_config=AppConfig(
                app_name="app_name",
                migrations_folder_path="/tmp/",
            )
        )
        self.assertEqual(
            migration_meta.migration_filename,
            "app_name_2022_01_10t07_15_20_003000",
        )
        self.assertEqual(
            migration_meta.migration_path,
            "/tmp/app_name_2022_01_10t07_15_20_003000.py",
        )

        # Try with an app name with invalid characters for a Python module.
        migration_meta = _generate_migration_meta(
            app_config=AppConfig(
                app_name="App-Name!",
                migrations_folder_path="/tmp/",
            )
        )
        self.assertEqual(
            migration_meta.migration_filename,
            "app_name_2022_01_10t07_15_20_003000",
        )
        self.assertEqual(
            migration_meta.migration_path,
            "/tmp/app_name_2022_01_10t07_15_20_003000.py",
        )
