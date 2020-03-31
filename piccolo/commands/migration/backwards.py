import asyncio
import sys

import click

from piccolo.migrations.auto import MigrationManager
from piccolo.migrations.tables import Migration
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

            _sorted_migration_ids = migration_ids[
                migration_ids.index(self.migration_name) :
            ]
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
                    migration_module.backwards()
                )  # type: ignore

                if isinstance(response, MigrationManager):
                    asyncio.run(response.run())

                Migration.delete().where(
                    Migration.name == migration_name
                ).run_sync()
        else:
            print("Not proceeding.")


@click.command()
@click.argument("app_name")
@click.argument("migration_name")
def backwards(migration_name: str, app_name: str):
    """
    Undo migrations up to a specific migrations. Specify a migration_name of
    'all' to undo all of the migrations.

    - make sure the migration name is valid
    - work out which to undo, and in which order
    - ask for confirmation
    - apply the undo operations one by one
    """
    manager = BackwardsMigrationManager(
        app_name=app_name, migration_name=migration_name
    )
    manager.run()
