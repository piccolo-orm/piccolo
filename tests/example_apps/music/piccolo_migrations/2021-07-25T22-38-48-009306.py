from enum import Enum

from piccolo.apps.migrations.auto import MigrationManager
from piccolo.columns.column_types import JSON, JSONB, Varchar
from piccolo.columns.indexes import IndexMethod

ID = "2021-07-25T22:38:48:009306"
VERSION = "0.26.0"


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="music")

    manager.add_table("Shirt", tablename="shirt")

    manager.add_table("RecordingStudio", tablename="recording_studio")

    manager.add_column(
        table_class_name="Shirt",
        tablename="shirt",
        column_name="size",
        column_class_name="Varchar",
        column_class=Varchar,
        params={
            "length": 1,
            "default": "l",
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": Enum(
                "Size", {"small": "s", "medium": "m", "large": "l"}
            ),
        },
    )

    manager.add_column(
        table_class_name="RecordingStudio",
        tablename="recording_studio",
        column_name="facilities",
        column_class_name="JSON",
        column_class=JSON,
        params={
            "default": "{}",
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
        },
    )

    manager.add_column(
        table_class_name="RecordingStudio",
        tablename="recording_studio",
        column_name="facilities_b",
        column_class_name="JSONB",
        column_class=JSONB,
        params={
            "default": "{}",
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
        },
    )

    return manager
