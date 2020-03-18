import click

from .base import BaseMigrationManager
from piccolo.migrations.tables import Migration


class CheckMigrationManager(BaseMigrationManager):
    def get_fixed_length_string(self, string: str, length=20) -> str:
        """
        Add spacing to the end of the string so it's a fixed length.
        """
        spacing = "".join([" " for i in range(20 - len(string))])
        fixed_length_string = f"{string}{spacing}"
        return fixed_length_string

    def run(self):
        print("Listing migrations ...")

        app_modules = self.get_app_modules()

        for app_module in app_modules:
            app_config = app_module.APP_CONFIG

            app_name = app_config.app_name
            fixed_length_app_name = self.get_fixed_length_string(app_name)

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
                print(f"{fixed_length_app_name} | {_id} | {has_ran}")


@click.command()
def check():
    """
    Lists all migrations which have and haven't ran.
    """
    CheckMigrationManager().run()
