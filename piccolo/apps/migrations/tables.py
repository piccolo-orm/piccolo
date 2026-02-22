from __future__ import annotations

from typing import Optional

from piccolo.columns import Timestamp, Varchar
from piccolo.columns.defaults.timestamp import TimestampNow
from piccolo.table import Table


class Migration(Table):
    name = Varchar(length=200)
    app_name = Varchar(length=200)
    ran_on = Timestamp(default=TimestampNow())

    @classmethod
    async def get_migrations_which_ran(
        cls, app_name: Optional[str] = None
    ) -> list[str]:
        """
        Returns the names of migrations which have already run, by inspecting
        the database.
        """
        query = cls.select(cls.name, cls.ran_on).order_by(cls.ran_on)
        if app_name is not None:
            query = query.where(cls.app_name == app_name)
        return [i["name"] for i in await query.run()]
