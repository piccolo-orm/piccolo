from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.base import OnDelete, OnUpdate
from piccolo.columns.column_types import ForeignKey, Serial, Varchar
from piccolo.columns.indexes import IndexMethod
from piccolo.table import Table


class RecordingStudio(Table, tablename="recording_studio", schema=None):
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


ID = "2024-05-28T23:15:41:018844"
VERSION = "1.5.1"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="music", description=DESCRIPTION
    )

    manager.add_table(
        class_name="Instrument",
        tablename="instrument",
        schema=None,
        columns=None,
    )

    manager.add_column(
        table_class_name="Instrument",
        tablename="instrument",
        column_name="name",
        db_column_name="name",
        column_class_name="Varchar",
        column_class=Varchar,
        params={
            "length": 255,
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
        table_class_name="Instrument",
        tablename="instrument",
        column_name="recording_studio",
        db_column_name="recording_studio",
        column_class_name="ForeignKey",
        column_class=ForeignKey,
        params={
            "references": RecordingStudio,
            "on_delete": OnDelete.cascade,
            "on_update": OnUpdate.cascade,
            "target_column": None,
            "null": True,
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
