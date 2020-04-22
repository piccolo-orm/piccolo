from .base import BaseMigrationManager
from piccolo.apps.migrations.tables import Migration
from piccolo.utils.printing import get_fixed_length_string


class CheckMigrationManager(BaseMigrationManager):
    def run(self):
        print("Listing migrations ...")

        # Make sure the migration table exists, otherwise we'll get an error.
        self.create_migration_table()

        print(
            f'{get_fixed_length_string("APP NAME")} | '
            f'{get_fixed_length_string("MIGRATION_ID")} | RAN'
        )

        app_modules = self.get_app_modules()

        for app_module in app_modules:
            app_config = app_module.APP_CONFIG

            app_name = app_config.app_name
            fixed_length_app_name = get_fixed_length_string(app_name)

            migration_modules = self.get_migration_modules(
                app_config.migrations_folder_path
            )
            ids = self.get_migration_ids(migration_modules)
            for _id in ids:
                has_ran = (
                    Migration.exists()
                    .where(
                        (Migration.name == _id)
                        & (Migration.app_name == app_name)
                    )
                    .run_sync()
                )
                fixed_length_id = get_fixed_length_string(_id)
                print(
                    f"{fixed_length_app_name} | {fixed_length_id} | {has_ran}"
                )


def check():
    """
    Lists all migrations which have and haven't ran.
    """
    CheckMigrationManager().run()
