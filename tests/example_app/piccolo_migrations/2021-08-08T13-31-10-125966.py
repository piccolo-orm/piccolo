from piccolo.apps.migrations.auto import MigrationManager
from piccolo.columns.column_types import UUID
from piccolo.columns.column_types import Varchar
from piccolo.columns.defaults.uuid import UUID4
from piccolo.columns.indexes import IndexMethod


ID = "2021-08-08T13:31:10:125966"
VERSION = "0.29.0"


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="example_app")

    manager.add_table("Album", tablename="album")

    manager.add_column(
        table_class_name="Album",
        tablename="album",
        column_name="id",
        column_class_name="UUID",
        column_class=UUID,
        params={
            "default": UUID4(),
            "null": False,
            "primary_key": True,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
        },
    )

    manager.add_column(
        table_class_name="Album",
        tablename="album",
        column_name="name",
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
        },
    )

    return manager
