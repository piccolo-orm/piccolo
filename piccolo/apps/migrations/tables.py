from __future__ import annotations

import typing as t

from piccolo.apps.migrations.auto.migration_manager import sort_table_classes
from piccolo.columns import Timestamp, Varchar
from piccolo.columns.defaults.timestamp import TimestampNow
from piccolo.query import Create
from piccolo.table import Table


class Migration(Table):
    name = Varchar(length=200)
    app_name = Varchar(length=200)
    ran_on = Timestamp(default=TimestampNow())

    @classmethod
    async def get_migrations_which_ran(
        cls, app_name: t.Optional[str] = None
    ) -> t.List[str]:
        """
        Returns the names of migrations which have already run, by inspecting
        the database.
        """
        query = cls.select(cls.name, cls.ran_on).order_by(cls.ran_on)
        if app_name is not None:
            query = query.where(cls.app_name == app_name)
        return [i["name"] for i in await query.run()]


def create_tables(*args: t.Type[Table], if_not_exists: bool = False) -> None:
    """
    Creates multiple tables that passed to it.
    """
    sorted_tables = sort_table_classes(list(args))
    for table in sorted_tables:
        Create(table=table, if_not_exists=if_not_exists).run_sync()
