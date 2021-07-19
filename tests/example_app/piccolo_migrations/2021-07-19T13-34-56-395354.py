from piccolo.apps.migrations.auto import MigrationManager
from decimal import Decimal
from piccolo.columns.base import OnDelete
from piccolo.columns.base import OnUpdate
from piccolo.columns.column_types import ForeignKey
from piccolo.columns.column_types import Integer
from piccolo.columns.column_types import Numeric
from piccolo.columns.column_types import Text
from piccolo.columns.column_types import Varchar
from piccolo.columns.indexes import IndexMethod
from piccolo.table import Table


class Band(Table, tablename="band"):
    pass


class Manager(Table, tablename="manager"):
    pass


class Venue(Table, tablename="venue"):
    pass


ID = "2021-07-19T13:34:56:395354"
VERSION = "0.26.0"


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="example_app")

    manager.add_column(
        table_class_name="Manager",
        tablename="manager",
        column_name="name",
        column_class_name="Varchar",
        column_class=Varchar,
        params={
            "length": 50,
            "default": "",
            "null": False,
            "primary": False,
            "key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
        },
    )

    manager.add_column(
        table_class_name="Band",
        tablename="band",
        column_name="name",
        column_class_name="Varchar",
        column_class=Varchar,
        params={
            "length": 50,
            "default": "",
            "null": False,
            "primary": False,
            "key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
        },
    )

    manager.add_column(
        table_class_name="Band",
        tablename="band",
        column_name="popularity",
        column_class_name="Integer",
        column_class=Integer,
        params={
            "default": 0,
            "null": False,
            "primary": False,
            "key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
        },
    )

    manager.add_column(
        table_class_name="Band",
        tablename="band",
        column_name="manager",
        column_class_name="ForeignKey",
        column_class=ForeignKey,
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
            "index_method": IndexMethod.btree,
            "choices": None,
        },
    )

    manager.add_column(
        table_class_name="Venue",
        tablename="venue",
        column_name="name",
        column_class_name="Varchar",
        column_class=Varchar,
        params={
            "length": 100,
            "default": "",
            "null": False,
            "primary": False,
            "key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
        },
    )

    manager.add_column(
        table_class_name="Venue",
        tablename="venue",
        column_name="capacity",
        column_class_name="Integer",
        column_class=Integer,
        params={
            "default": 0,
            "null": False,
            "primary": False,
            "key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
        },
    )

    manager.add_column(
        table_class_name="Concert",
        tablename="concert",
        column_name="venue",
        column_class_name="ForeignKey",
        column_class=ForeignKey,
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
            "index_method": IndexMethod.btree,
            "choices": None,
        },
    )

    manager.add_column(
        table_class_name="Concert",
        tablename="concert",
        column_name="band_2",
        column_class_name="ForeignKey",
        column_class=ForeignKey,
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
            "index_method": IndexMethod.btree,
            "choices": None,
        },
    )

    manager.add_column(
        table_class_name="Concert",
        tablename="concert",
        column_name="band_1",
        column_class_name="ForeignKey",
        column_class=ForeignKey,
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
            "index_method": IndexMethod.btree,
            "choices": None,
        },
    )

    manager.add_column(
        table_class_name="Ticket",
        tablename="ticket",
        column_name="price",
        column_class_name="Numeric",
        column_class=Numeric,
        params={
            "default": Decimal("0"),
            "digits": (5, 2),
            "null": False,
            "primary": False,
            "key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
        },
    )

    manager.add_column(
        table_class_name="Poster",
        tablename="poster",
        column_name="content",
        column_class_name="Text",
        column_class=Text,
        params={
            "default": "",
            "null": False,
            "primary": False,
            "key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
        },
    )

    return manager
