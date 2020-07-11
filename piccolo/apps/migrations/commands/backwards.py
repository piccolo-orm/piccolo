import asyncio
import sys

from piccolo.apps.migrations.auto import MigrationManager
from piccolo.apps.migrations.tables import Migration
from .base import BaseMigrationManager


class BackwardsMigrationManager(BaseMigrationManager):
    def __init__(self, app_name: str, migration_id: str):
        self.migration_id = migration_id
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

        ran_migration_ids = Migration.get_migrations_which_ran(
            app_name=self.app_name
        )
        if len(ran_migration_ids) == 0:
            sys.exit("No migrations to reverse!")

        #######################################################################

        if self.migration_id == "all":
            earliest_migration_id = ran_migration_ids[0]
        else:
            earliest_migration_id = self.migration_id

        if earliest_migration_id not in ran_migration_ids:
            print(
                "Unrecognized migration name - must be one of "
                f"{ran_migration_ids}"
            )

        #######################################################################

        latest_migration_id = ran_migration_ids[-1]

        start_index = ran_migration_ids.index(earliest_migration_id)
        end_index = ran_migration_ids.index(latest_migration_id) + 1

        subset = ran_migration_ids[start_index:end_index]
        reversed_migration_ids = list(reversed(subset))

        #######################################################################

        _continue = input(
            "About to undo the following migrations:\n"
            f"{reversed_migration_ids}\n"
            "Enter y to continue.\n"
        )
        if _continue == "y":
            print("Undoing migrations")

            for migration_id in reversed_migration_ids:
                print(f"Reversing {migration_id}")
                migration_module = migration_modules[migration_id]
                response = asyncio.run(
                    migration_module.forwards()
                )  # type: ignore

                if isinstance(response, MigrationManager):
                    asyncio.run(response.run_backwards())

                Migration.delete().where(
                    Migration.name == migration_id
                ).run_sync()
        else:
            print("Not proceeding.")


def backwards(app_name: str, migration_id: str):
    """
    Undo migrations up to a specific migration.

    :param app_name:
        The app to reverse migrations for.
    :param migration_id:
        Migrations will be reversed up to this migration. Specify a value of
        'all' to undo all of the migrations.
    """
    manager = BackwardsMigrationManager(
        app_name=app_name, migration_id=migration_id
    )
    manager.run()
