from __future__ import annotations
import typing as t

from piccolo.custom_types import DatetimeDefault
from piccolo.table import Table
from piccolo.columns import Varchar, Timestamp


class Migration(Table):
    name = Varchar(length=200)
    app_name = Varchar(length=200)
    ran_on = Timestamp(default=DatetimeDefault.now)

    @classmethod
    def get_migrations_which_ran(cls) -> t.List[str]:
        """
        Returns the names of migrations which have already run, by inspecting
        the database.
        """
        return [i["name"] for i in cls.select(cls.name).run_sync()]
