import os

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

        config_modules = self.get_config_modules()

        for config_module in config_modules:
            app_name = self.get_app_name(config_module)
            fixed_length_app_name = self.get_fixed_length_string(app_name)

            path = os.path.dirname(config_module.__file__)
            migration_modules = self.get_migration_modules(path)
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
