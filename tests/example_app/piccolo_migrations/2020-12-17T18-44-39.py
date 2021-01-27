from piccolo.apps.migrations.auto import MigrationManager
from decimal import Decimal
from piccolo.columns.base import OnDelete
from piccolo.columns.base import OnUpdate
from piccolo.table import Table


class Band(Table, tablename="band"):
    pass


class Venue(Table, tablename="venue"):
    pass


ID = "2020-12-17T18:44:39"
VERSION = "0.14.7"


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="example_app")

    manager.add_table("Ticket", tablename="ticket")
    manager.add_table("Venue", tablename="venue")
    manager.add_table("Concert", tablename="concert")

    manager.add_column(
        table_class_name="Ticket",
        tablename="ticket",
        column_name="price",
        column_class_name="Numeric",
        params={
            "default": Decimal("0"),
            "digits": (5, 2),
            "null": False,
            "primary": False,
            "key": False,
            "unique": False,
            "index": False,
        },
    )

    manager.add_column(
        table_class_name="Concert",
        tablename="concert",
        column_name="band_1",
        column_class_name="ForeignKey",
        params={
            "references": Band,
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
        table_class_name="Concert",
        tablename="concert",
        column_name="band_2",
        column_class_name="ForeignKey",
        params={
            "references": Band,
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
        table_class_name="Concert",
        tablename="concert",
        column_name="venue",
        column_class_name="ForeignKey",
        params={
            "references": Venue,
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
        table_class_name="Venue",
        tablename="venue",
        column_name="name",
        column_class_name="Varchar",
        params={
            "length": 100,
            "default": "",
            "null": False,
            "primary": False,
            "key": False,
            "unique": False,
            "index": False,
        },
    )

    manager.add_column(
        table_class_name="Venue",
        tablename="venue",
        column_name="capacity",
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

    return manager
