from __future__ import annotations

import datetime
import os
import shutil
import tempfile
import time
import typing as t
import uuid
from unittest import TestCase

from piccolo.apps.migrations.commands.forwards import ForwardsMigrationManager
from piccolo.apps.migrations.commands.new import (
    _create_migrations_folder,
    _create_new_migration,
)
from piccolo.apps.migrations.tables import Migration
from piccolo.columns.column_types import (
    JSON,
    JSONB,
    UUID,
    Array,
    BigInt,
    Boolean,
    Date,
    DoublePrecision,
    Integer,
    Interval,
    Real,
    SmallInt,
    Text,
    Time,
    Timestamp,
    Varchar,
)
from piccolo.columns.defaults.uuid import UUID4
from piccolo.conf.apps import AppConfig
from piccolo.table import Table, create_table_class
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


def datetime_default():
    return datetime.datetime.now()


def time_default():
    return datetime.datetime.now().time()


def date_default():
    return datetime.datetime.now().date()


def timedelta_default():
    return datetime.timedelta(days=1)


def boolean_default():
    return True


def array_default_integer():
    return [4, 5, 6]


def array_default_varchar():
    return ["x", "y", "z"]


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

    def test_real_column(self):
        self._test_migrations(
            table_classes=[
                self.table(column)
                for column in [
                    Real(),
                    Real(default=1.1),
                    Real(null=True),
                    Real(null=False),
                    Real(index=True),
                    Real(index=False),
                ]
            ]
        )

    def test_double_precision_column(self):
        self._test_migrations(
            table_classes=[
                self.table(column)
                for column in [
                    DoublePrecision(),
                    DoublePrecision(default=1.1),
                    DoublePrecision(null=True),
                    DoublePrecision(null=False),
                    DoublePrecision(index=True),
                    DoublePrecision(index=False),
                ]
            ]
        )

    def test_smallint_column(self):
        self._test_migrations(
            table_classes=[
                self.table(column)
                for column in [
                    SmallInt(),
                    SmallInt(default=1),
                    SmallInt(default=integer_default),
                    SmallInt(null=True),
                    SmallInt(null=False),
                    SmallInt(index=True),
                    SmallInt(index=False),
                ]
            ]
        )

    def test_bigint_column(self):
        self._test_migrations(
            table_classes=[
                self.table(column)
                for column in [
                    BigInt(),
                    BigInt(default=1),
                    BigInt(default=integer_default),
                    BigInt(null=True),
                    BigInt(null=False),
                    BigInt(index=True),
                    BigInt(index=False),
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
                    UUID(null=True, default=None),
                    UUID(null=False),
                    UUID(index=True),
                    UUID(index=False),
                ]
            ]
        )

    def test_timestamp_column(self):
        self._test_migrations(
            table_classes=[
                self.table(column)
                for column in [
                    Timestamp(),
                    Timestamp(
                        default=datetime.datetime(year=2021, month=1, day=1)
                    ),
                    Timestamp(default=datetime.datetime.now),
                    Timestamp(default=datetime_default),
                    Timestamp(null=True, default=None),
                    Timestamp(null=False),
                    Timestamp(index=True),
                    Timestamp(index=False),
                ]
            ]
        )

    def test_time_column(self):
        self._test_migrations(
            table_classes=[
                self.table(column)
                for column in [
                    Time(),
                    Time(default=datetime.time(hour=12, minute=0)),
                    Time(default=datetime.time),
                    Time(default=time_default),
                    Time(null=True, default=None),
                    Time(null=False),
                    Time(index=True),
                    Time(index=False),
                ]
            ]
        )

    def test_date_column(self):
        self._test_migrations(
            table_classes=[
                self.table(column)
                for column in [
                    Date(),
                    Date(default=datetime.date(year=2021, month=1, day=1)),
                    Date(default=datetime.date.today),
                    Date(default=date_default),
                    Date(null=True, default=None),
                    Date(null=False),
                    Date(index=True),
                    Date(index=False),
                ]
            ]
        )

    def test_interval_column(self):
        self._test_migrations(
            table_classes=[
                self.table(column)
                for column in [
                    Interval(),
                    Interval(default=datetime.timedelta(days=1)),
                    Interval(default=timedelta_default),
                    Interval(null=True, default=None),
                    Interval(null=False),
                    Interval(index=True),
                    Interval(index=False),
                ]
            ]
        )

    def test_boolean_column(self):
        self._test_migrations(
            table_classes=[
                self.table(column)
                for column in [
                    Boolean(),
                    Boolean(default=True),
                    Boolean(default=boolean_default),
                    Boolean(null=True, default=None),
                    Boolean(null=False),
                    Boolean(index=True),
                    Boolean(index=False),
                ]
            ]
        )

    def test_array_column_integer(self):
        self._test_migrations(
            table_classes=[
                self.table(column)
                for column in [
                    Array(base_column=Integer()),
                    Array(base_column=Integer(), default=[1, 2, 3]),
                    Array(
                        base_column=Integer(), default=array_default_integer
                    ),
                    Array(base_column=Integer(), null=True, default=None),
                    Array(base_column=Integer(), null=False),
                    Array(base_column=Integer(), index=True),
                    Array(base_column=Integer(), index=False),
                ]
            ]
        )

    def test_array_column_varchar(self):
        self._test_migrations(
            table_classes=[
                self.table(column)
                for column in [
                    Array(base_column=Varchar()),
                    Array(base_column=Varchar(), default=["a", "b", "c"]),
                    Array(
                        base_column=Varchar(), default=array_default_varchar
                    ),
                    Array(base_column=Varchar(), null=True, default=None),
                    Array(base_column=Varchar(), null=False),
                    Array(base_column=Varchar(), index=True),
                    Array(base_column=Varchar(), index=False),
                ]
            ]
        )

    ###########################################################################

    # We deliberately don't test setting JSON or JSONB columns as indexes, as
    # we know it'll fail.

    def test_json_column(self):
        self._test_migrations(
            table_classes=[
                self.table(column)
                for column in [
                    JSON(),
                    JSON(default=["a", "b", "c"]),
                    JSON(default={"name": "bob"}),
                    JSON(default='{"name": "Sally"}'),
                    JSON(null=True, default=None),
                    JSON(null=False),
                ]
            ]
        )

    def test_jsonb_column(self):
        self._test_migrations(
            table_classes=[
                self.table(column)
                for column in [
                    JSONB(),
                    JSONB(default=["a", "b", "c"]),
                    JSONB(default={"name": "bob"}),
                    JSONB(default='{"name": "Sally"}'),
                    JSONB(null=True, default=None),
                    JSONB(null=False),
                ]
            ]
        )
