from piccolo.apps.migrations.auto import MigrationManager
from piccolo.columns.base import OnDelete, OnUpdate
from piccolo.columns.column_types import ForeignKey, Serial
from piccolo.columns.indexes import IndexMethod
from piccolo.table import Table


class Concert(Table, tablename="concert"):
    id = Serial(
        null=False,
        primary_key=True,
        unique=False,
        index=False,
        index_method=IndexMethod.btree,
        choices=None,
    )


ID = "2021-09-06T13:58:23:024723"
VERSION = "0.43.0"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="example_app", description=DESCRIPTION
    )

    manager.add_column(
        table_class_name="Ticket",
        tablename="ticket",
        column_name="concert",
        column_class_name="ForeignKey",
        column_class=ForeignKey,
        params={
            "references": Concert,
            "on_delete": OnDelete.cascade,
            "on_update": OnUpdate.cascade,
            "null": True,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
        },
    )

    return manager
