import asyncio
import sys

from piccolo.apps.migrations.auto import MigrationManager
from piccolo.apps.migrations.tables import Migration
from .base import BaseMigrationManager


class BackwardsMigrationManager(BaseMigrationManager):
    def __init__(self, app_name: str, migration_name: str):
        self.migration_name = migration_name
        self.app_name = app_name

    def run(self):
        app_modules = self.get_app_modules()

        migration_modules = []

        for app_module in app_modules:
            app_config = getattr(app_module, "APP_CONFIG")
            if app_config.app_name == self.app_name:
                migration_modules = self.get_migration_modules(
                    app_config.migrations_folder_path
                )
                break

        migration_ids = self.get_migration_ids(migration_modules)

        if self.migration_name == "all":
            self.migration_name = migration_ids[0]

        if self.migration_name not in migration_ids:
            print(
                f"Unrecognized migration name - must be one of {migration_ids}"
            )

        _continue = input(
            "About to undo the migrations - press y to continue."
        )
        if _continue == "y":
            print("Undoing migrations")

            index = migration_ids.index(self.migration_name)
            _sorted_migration_ids = migration_ids[index:]
            _sorted_migration_ids.reverse()

            already_ran = Migration.get_migrations_which_ran()

            for migration_name in _sorted_migration_ids:
                if migration_name not in already_ran:
                    print(
                        f"Migration {migration_name} hasn't run yet, can't "
                        "undo!"
                    )
                    sys.exit(1)

                print(f"Reversing {migration_name}")
                migration_module = migration_modules[migration_name]
                response = asyncio.run(
                    migration_module.forwards()
                )  # type: ignore

                if isinstance(response, MigrationManager):
                    asyncio.run(response.run_backwards())

                Migration.delete().where(
                    Migration.name == migration_name
                ).run_sync()
        else:
            print("Not proceeding.")


def backwards(app_name: str, migration_name: str):
    """
    Undo migrations up to a specific migration.

    :param app_name:
        The app to reverse migrations for.
    :param migration_name:
        Migrations will be reversed up to this migration. Specify a value of
        'all' to undo all of the migrations.
    """
    manager = BackwardsMigrationManager(
        app_name=app_name, migration_name=migration_name
    )
    manager.run()
