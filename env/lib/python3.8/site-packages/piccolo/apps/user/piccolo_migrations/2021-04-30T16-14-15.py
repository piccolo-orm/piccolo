from piccolo.apps.migrations.auto import MigrationManager
from piccolo.columns.column_types import Boolean, Timestamp
from piccolo.columns.indexes import IndexMethod

ID = "2021-04-30T16:14:15"
VERSION = "0.18.2"


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="user")

    manager.add_column(
        table_class_name="BaseUser",
        tablename="piccolo_user",
        column_name="superuser",
        column_class_name="Boolean",
        column_class=Boolean,
        params={
            "default": False,
            "null": False,
            "primary": False,
            "key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
        },
    )

    manager.add_column(
        table_class_name="BaseUser",
        tablename="piccolo_user",
        column_name="last_login",
        column_class_name="Timestamp",
        column_class=Timestamp,
        params={
            "default": None,
            "null": True,
            "primary": False,
            "key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
        },
    )

    return manager
