from __future__ import annotations
import os
import shutil
import tempfile
import time
import typing as t
from unittest import TestCase
import uuid

from piccolo.columns.defaults.uuid import UUID4
from piccolo.conf.apps import AppConfig
from piccolo.columns.column_types import Integer, Text, UUID, Varchar
from piccolo.apps.migrations.commands.new import (
    _create_new_migration,
    _create_migrations_folder,
)
from piccolo.apps.migrations.commands.forwards import ForwardsMigrationManager
from piccolo.table import Table, create_table_class
from piccolo.apps.migrations.tables import Migration
from piccolo.utils.sync import run_sync
from tests.base import postgres_only

if t.TYPE_CHECKING:
    from piccolo.columns.base import Column


def string_default():
    return "hello world"


def integer_default():
    return 1


def uuid_default():
    return uuid.uuid4()


@postgres_only
class TestMigrations(TestCase):
    def tearDown(self):
        create_table_class("MyTable").alter().drop_table(
            if_exists=True
        ).run_sync()
        Migration.alter().drop_table(if_exists=True).run_sync()

    def run_migrations(self, app_config: AppConfig):
        manager = ForwardsMigrationManager(app_name=app_config.app_name)
        run_sync(manager.create_migration_table())
        run_sync(manager.run_migrations(app_config=app_config))

    def _test_migrations(self, table_classes: t.List[t.Type[Table]]):
        temp_directory_path = tempfile.gettempdir()
        migrations_folder_path = os.path.join(
            temp_directory_path, "piccolo_migrations"
        )

        if os.path.exists(migrations_folder_path):
            shutil.rmtree(migrations_folder_path)

        _create_migrations_folder(migrations_folder_path)

        app_config = AppConfig(
            app_name="test_app",
            migrations_folder_path=migrations_folder_path,
            table_classes=[],
        )

        for table_class in table_classes:
            app_config.table_classes = [table_class]
            meta = run_sync(
                _create_new_migration(app_config=app_config, auto=True)
            )
            self.assertTrue(os.path.exists(meta.migration_path))
            self.run_migrations(app_config=app_config)

            # It's kind of absurd sleeping for 1 microsecond, but it guarantees
            # the migration IDs will be unique, and just in case computers
            # and / or Python get insanely fast in the future :)
            time.sleep(1e-6)

            # TODO - check the migrations ran correctly

    ###########################################################################

    def table(self, column: Column):
        return create_table_class(
            class_name="MyTable", class_members={"my_column": column}
        )

    def test_varchar_column(self):
        self._test_migrations(
            table_classes=[
                self.table(column)
                for column in [
                    Varchar(),
                    Varchar(length=100),
                    Varchar(default="hello world"),
                    Varchar(default=string_default),
                    Varchar(null=True),
                    Varchar(null=False),
                    Varchar(index=True),
                    Varchar(index=False),
                ]
            ]
        )

    def test_text_column(self):
        self._test_migrations(
            table_classes=[
                self.table(column)
                for column in [
                    Text(),
                    Text(default="hello world"),
                    Text(default=string_default),
                    Text(null=True),
                    Text(null=False),
                    Text(index=True),
                    Text(index=False),
                ]
            ]
        )

    def test_integer_column(self):
        self._test_migrations(
            table_classes=[
                self.table(column)
                for column in [
                    Integer(),
                    Integer(default=1),
                    Integer(default=integer_default),
                    Integer(null=True),
                    Integer(null=False),
                    Integer(index=True),
                    Integer(index=False),
                ]
            ]
        )

    def test_uuid_column(self):
        self._test_migrations(
            table_classes=[
                self.table(column)
                for column in [
                    UUID(),
                    UUID(default="ecf338cd-6da7-464c-b31e-4b2e3e12f0f0"),
                    UUID(
                        default=uuid.UUID(
                            "2dfc9c47-adab-4692-b804-f692f3b0fc07"
                        )
                    ),
                    UUID(default=uuid.uuid4),
                    UUID(default=uuid_default),
                    UUID(default=UUID4()),
                    UUID(null=True),
                    UUID(null=False),
                    UUID(index=True),
                    UUID(index=False),
                ]
            ]
        )
