import os
import shutil
from unittest import TestCase

from piccolo.apps.migrations.commands.base import AppConfig
from piccolo.apps.migrations.commands.new import (
    _create_new_migration,
    BaseMigrationManager,
)

from tests.example_project.tables import Manager


class TestNewMigrationCommand(TestCase):
    def test_create_new_migration(self):
        migration_folder = "/tmp/piccolo_migrations/"

        if os.path.exists(migration_folder):
            shutil.rmtree(migration_folder)

        os.mkdir(migration_folder)

        app_config = AppConfig(
            app_name="music",
            migrations_folder_path=migration_folder,
            table_classes=[Manager],
        )

        _create_new_migration(app_config, auto=False)

        migration_modules = BaseMigrationManager().get_migration_modules(
            migration_folder
        )

        self.assertTrue(len(migration_modules.keys()) == 1)
