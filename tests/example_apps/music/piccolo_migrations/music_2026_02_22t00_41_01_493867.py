from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.base import OnDelete, OnUpdate
from piccolo.columns.column_types import ForeignKey, Serial, Text, Timestamptz
from piccolo.columns.defaults.timestamptz import TimestamptzNow
from piccolo.columns.indexes import IndexMethod
from piccolo.table import Table


class Band(Table, tablename="band", schema=None):
    id = Serial(
        null=False,
        primary_key=True,
        unique=False,
        index=False,
        index_method=IndexMethod.btree,
        choices=None,
        db_column_name="id",
        secret=False,
    )


ID = "2026-02-22T00:41:01:493867"
VERSION = "1.32.0"
DESCRIPTION = "Add Signing table"


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="music", description=DESCRIPTION
    )

    manager.add_table(
        class_name="Signing", tablename="signing", schema=None, columns=None
    )

    manager.add_column(
        table_class_name="Signing",
        tablename="signing",
        column_name="address",
        db_column_name="address",
        column_class_name="Text",
        column_class=Text,
        params={
            "default": "",
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    manager.add_column(
        table_class_name="Signing",
        tablename="signing",
        column_name="with_",
        db_column_name="with",
        column_class_name="ForeignKey",
        column_class=ForeignKey,
        params={
            "references": Band,
            "on_delete": OnDelete.cascade,
            "on_update": OnUpdate.cascade,
            "target_column": None,
            "null": True,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": "with",
            "secret": False,
        },
        schema=None,
    )

    manager.add_column(
        table_class_name="Signing",
        tablename="signing",
        column_name="starts",
        db_column_name="starts",
        column_class_name="Timestamptz",
        column_class=Timestamptz,
        params={
            "default": TimestamptzNow(),
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    return manager
