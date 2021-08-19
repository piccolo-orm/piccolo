import dataclasses
import typing as t

from piccolo.apps.migrations.commands.base import BaseMigrationManager
from piccolo.apps.migrations.tables import Migration
from piccolo.utils.printing import get_fixed_length_string


@dataclasses.dataclass
class MigrationStatus:
    app_name: str
    migration_id: str
    description: str
    has_ran: bool


class CheckMigrationManager(BaseMigrationManager):
    def __init__(self, app_name: str):
        self.app_name = app_name
        super().__init__()

    async def get_migration_statuses(self) -> t.List[MigrationStatus]:
        # Make sure the migration table exists, otherwise we'll get an error.
        await self.create_migration_table()

        migration_statuses: t.List[MigrationStatus] = []

        app_modules = self.get_app_modules()

        for app_module in app_modules:
            app_config = app_module.APP_CONFIG

            app_name = app_config.app_name

            if (self.app_name != "all") and (self.app_name != app_name):
                continue

            migration_modules = self.get_migration_modules(
                app_config.migrations_folder_path
            )
            ids = self.get_migration_ids(migration_modules)
            for _id in ids:
                has_ran = (
                    await Migration.exists()
                    .where(
                        (Migration.name == _id)
                        & (Migration.app_name == app_name)
                    )
                    .run()
                )
                description = getattr(
                    migration_modules[_id], "DESCRIPTION", "-"
                )
                migration_statuses.append(
                    MigrationStatus(
                        app_name=app_name,
                        migration_id=_id,
                        description=description,
                        has_ran=has_ran,
                    )
                )

        return migration_statuses

    async def have_ran_count(self) -> int:
        """
        :returns:
            The number of migrations which have been ran.
        """
        migration_statuses = await self.get_migration_statuses()
        return len([i for i in migration_statuses if i.has_ran])

    async def havent_ran_count(self) -> int:
        """
        :returns:
            The number of migrations which haven't been ran.
        """
        migration_statuses = await self.get_migration_statuses()
        return len([i for i in migration_statuses if not i.has_ran])

    async def run(self):
        """
        Prints out the migrations which have and haven't ran.
        """
        print("Listing migrations ...")
        desc_length = 40
        id_length = 26

        print(
            f'{get_fixed_length_string("APP NAME")} | '
            f'{get_fixed_length_string("MIGRATION_ID", id_length)} | '
            f'{get_fixed_length_string("DESCRIPTION", desc_length)} | RAN'
        )

        migration_statuses = await self.get_migration_statuses()

        for migration_status in migration_statuses:
            fixed_length_app_name = get_fixed_length_string(
                migration_status.app_name
            )
            fixed_length_id = get_fixed_length_string(
                migration_status.migration_id, length=id_length
            )
            fixed_length_description = get_fixed_length_string(
                migration_status.description, desc_length
            )
            has_ran = migration_status.has_ran
            print(
                f"{fixed_length_app_name} | "
                f"{fixed_length_id} | "
                f"{fixed_length_description} | "
                f"{has_ran}"
            )


async def check(app_name: str = "all"):
    """
    Lists all migrations which have and haven't ran.

    :param app_name:
        The name of the app to check. Specify a value of 'all' to check
        the migrations for all apps.
    """
    await CheckMigrationManager(app_name=app_name).run()
