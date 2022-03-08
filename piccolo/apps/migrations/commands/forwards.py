from __future__ import annotations

import sys
import typing as t

from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.apps.migrations.commands.base import (
    BaseMigrationManager,
    MigrationResult,
)
from piccolo.apps.migrations.tables import Migration
from piccolo.conf.apps import AppConfig, MigrationModule


class ForwardsMigrationManager(BaseMigrationManager):
    def __init__(
        self, app_name: str, migration_id: str = "all", fake: bool = False
    ):
        self.app_name = app_name
        self.migration_id = migration_id
        self.fake = fake
        super().__init__()

    async def run_migrations(self, app_config: AppConfig) -> MigrationResult:
        already_ran = await Migration.get_migrations_which_ran(
            app_name=app_config.app_name
        )

        migration_modules: t.Dict[
            str, MigrationModule
        ] = self.get_migration_modules(app_config.migrations_folder_path)

        ids = self.get_migration_ids(migration_modules)
        n = len(ids)
        print(f"👍 {n} migration{'s' if n != 1 else ''} already complete")

        havent_run = sorted(set(ids) - set(already_ran))
        if len(havent_run) == 0:
            # Make sure this still appears successful, as we don't want this
            # to appear as an error in automated scripts.
            message = "🏁 No migrations need to be run"
            print(message)
            return MigrationResult(success=True, message=message)
        else:
            n = len(havent_run)
            print(f"⏩ {n} migration{'s' if n != 1 else ''} not yet run")

        if self.migration_id == "all":
            subset = havent_run
        elif self.migration_id == "1":
            subset = havent_run[:1]
        else:
            try:
                index = havent_run.index(self.migration_id)
            except ValueError:
                message = f"{self.migration_id} is unrecognised"
                print(message, file=sys.stderr)
                return MigrationResult(success=False, message=message)
            else:
                subset = havent_run[: index + 1]

        if subset:
            n = len(subset)
            print(f"🚀 Running {n} migration{'s' if n != 1 else ''}:")

            for _id in subset:
                if self.fake:
                    print(f"- {_id}: faked! ⏭️")
                else:
                    migration_module = migration_modules[_id]
                    response = await migration_module.forwards()

                    if isinstance(response, MigrationManager):
                        await response.run()

                    print("ok! ✔️")

                await Migration.insert().add(
                    Migration(name=_id, app_name=app_config.app_name)
                ).run()

        return MigrationResult(success=True, message="migration succeeded")

    async def run(self) -> MigrationResult:
        await self.create_migration_table()

        app_config = self.get_app_config(app_name=self.app_name)

        return await self.run_migrations(app_config)


async def run_forwards(
    app_name: str, migration_id: str = "all", fake: bool = False
) -> MigrationResult:
    """
    Run the migrations. This function can be used to programatically run
    migrations - for example, in a unit test.
    """
    if app_name == "all":
        sorted_app_names = BaseMigrationManager().get_sorted_app_names()
        for _app_name in sorted_app_names:
            print(f"\n{_app_name.upper():^64}")
            print("-" * 64)
            manager = ForwardsMigrationManager(
                app_name=_app_name, migration_id="all", fake=fake
            )
            response = await manager.run()
            if not response.success:
                return response

        return MigrationResult(success=True)

    else:
        manager = ForwardsMigrationManager(
            app_name=app_name, migration_id=migration_id, fake=fake
        )
        return await manager.run()


async def forwards(
    app_name: str, migration_id: str = "all", fake: bool = False
):
    """
    Runs any migrations which haven't been run yet.

    :param app_name:
        The name of the app to migrate. Specify a value of 'all' to run
        migrations for all apps.
    :param migration_id:
        Migrations will be ran up to and including this migration_id.
        Specify a value of 'all' to run all of the migrations. Specify a
        value of '1' to just run the next migration.
    :param fake:
        If set, will record the migrations as being run without actually
        running them.
    """
    response = await run_forwards(
        app_name=app_name, migration_id=migration_id, fake=fake
    )

    if not response.success:
        sys.exit(1)
