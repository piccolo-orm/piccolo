from __future__ import annotations
import asyncio
import typing as t

from .base import (
    BaseMigrationManager,
    MigrationModule,
)
from piccolo.conf.apps import AppConfig
from piccolo.apps.migrations.tables import Migration
from piccolo.apps.migrations.auto import MigrationManager


class ForwardsMigrationManager(BaseMigrationManager):
    def __init__(self, app_name: str, fake: bool = False, *args, **kwargs):
        self.app_name = app_name
        self.fake = fake

    def run_migrations(self, app_config: AppConfig) -> None:
        already_ran = Migration.get_migrations_which_ran()
        print(f"Already ran:\n{already_ran}\n")

        migration_modules: t.Dict[
            str, MigrationModule
        ] = self.get_migration_modules(app_config.migrations_folder_path)

        ids = self.get_migration_ids(migration_modules)
        print(f"Migration ids = {ids}")

        havent_run = sorted(set(ids) - set(already_ran))
        print(f"Haven't run = {havent_run}")

        for _id in havent_run:
            if self.fake:
                print(f"Faked {_id}")
            else:
                migration_module = migration_modules[_id]
                response = asyncio.run(migration_module.forwards())

                if isinstance(response, MigrationManager):
                    asyncio.run(response.run())

                print(f"Ran {_id}")

            Migration.insert().add(
                Migration(name=_id, app_name=self.app_name)
            ).run_sync()

    def run(self):
        print("Running migrations ...")
        self.create_migration_table()

        app_config = self.get_app_config(app_name=self.app_name)

        self.run_migrations(app_config)


def forwards(app_name: str, fake: bool = False):
    """
    Runs any migrations which haven't been run yet.

    :param app_name:
        The name of the app to migrate.
    :param fake:
        If set, will record the migrations as being run without actually
        running them.
    """
    manager = ForwardsMigrationManager(app_name=app_name, fake=fake)
    manager.run()
