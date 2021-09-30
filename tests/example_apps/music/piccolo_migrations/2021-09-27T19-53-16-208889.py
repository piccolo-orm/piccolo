from piccolo.apps.migrations.auto import MigrationManager
from enum import Enum
from piccolo.columns.column_types import Varchar
from piccolo.columns.indexes import IndexMethod


ID = "2021-09-27T19:53:16:208889"
VERSION = "0.51.1"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="example_app", description=DESCRIPTION
    )

    manager.add_column(
        table_class_name="Shirt",
        tablename="shirt",
        column_name="size2",
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
            "choices": Enum("Size", {"small": "s", "medium": "m", "large": "l"}),
        },
    )

    return manager
