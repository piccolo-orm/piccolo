from piccolo.apps.migrations.auto import MigrationManager
from piccolo.columns.base import OnDelete, OnUpdate
from piccolo.table import Table


class Manager(Table, tablename="manager"):
    pass


ID = "2020-12-17T18:44:30"
VERSION = "0.14.7"


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="example_app")

    manager.add_table("Manager", tablename="manager")
    manager.add_table("Band", tablename="band")

    manager.add_column(
        table_class_name="Band",
        tablename="band",
        column_name="name",
        column_class_name="Varchar",
        params={
            "length": 50,
            "default": "",
            "null": False,
            "primary": False,
            "key": False,
            "unique": False,
            "index": False,
        },
    )

    manager.add_column(
        table_class_name="Band",
        tablename="band",
        column_name="manager",
        column_class_name="ForeignKey",
        params={
            "references": Manager,
            "on_delete": OnDelete.cascade,
            "on_update": OnUpdate.cascade,
            "default": None,
            "null": True,
            "primary": False,
            "key": False,
            "unique": False,
            "index": False,
        },
    )

    manager.add_column(
        table_class_name="Band",
        tablename="band",
        column_name="popularity",
        column_class_name="Integer",
        params={
            "default": 0,
            "null": False,
            "primary": False,
            "key": False,
            "unique": False,
            "index": False,
        },
    )

    manager.add_column(
        table_class_name="Manager",
        tablename="manager",
        column_name="name",
        column_class_name="Varchar",
        params={
            "length": 50,
            "default": "",
            "null": False,
            "primary": False,
            "key": False,
            "unique": False,
            "index": False,
        },
    )

    return manager
