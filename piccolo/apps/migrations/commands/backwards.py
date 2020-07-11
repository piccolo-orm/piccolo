import asyncio

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
            print("No migrations to reverse!")
            return

        #######################################################################

        if self.migration_id == "all":
            earliest_migration_id = ran_migration_ids[0]
        elif self.migration_id == "1":
            earliest_migration_id = ran_migration_ids[-1]
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


def backwards(app_name: str, migration_id: str = "1"):
    """
    Undo migrations up to a specific migration.

    :param app_name:
        The app to reverse migrations for. Specify a value of 'all' to reverse
        migrations for all apps.
    :param migration_id:
        Migrations will be reversed up to and including this migration_id.
        Specify a value of 'all' to undo all of the migrations. Specify a
        value of '1' to undo the most recent migration.
    """
    if app_name == "all":
        sorted_app_names = BaseMigrationManager().get_sorted_app_names()
        sorted_app_names.reverse()

        _continue = input(
            "You're about to undo the migrations for the following apps:\n"
            f"{sorted_app_names}\n"
            "Are you sure you want to continue?\n"
            "Enter y to continue.\n"
        )
        if _continue == "y":
            for _app_name in sorted_app_names:
                print(f"Undoing {_app_name}")
                manager = BackwardsMigrationManager(
                    app_name=_app_name, migration_id="all"
                )
                manager.run()
    else:
        manager = BackwardsMigrationManager(
            app_name=app_name, migration_id=migration_id
        )
        manager.run()
