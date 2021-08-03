from __future__ import annotations

import typing as t

from piccolo.columns import Column, Selectable

NUMERIC_TYPES = (
    "BIGINT",
    "INTEGER",
    "NUMERIC",
    "REAL",
    "SMALLINT",
)


class Avg(Selectable):
    """
    AVG() SQL function. The column type must be numeric to run the query.

    await Band.select(Avg(Band.popularity)).run()
    """

    def __init__(self, column=t.Type[Column]):
        self.column = column

    def get_select_string(self, engine_type: str, just_alias=False) -> str:
        if self.column.column_type.split("(")[0] in NUMERIC_TYPES:
            column_name = self.column._meta.get_full_name(
                just_alias=just_alias
            )
        else:
            raise Exception(
                "The column type must be numeric to run the query."
            )
        return f"AVG({column_name}) AS avg"


class Max(Selectable):
    """
    MAX() SQL function. The column type must be numeric to run the query.

    await Band.select(Max(Band.popularity)).run()
    """

    def __init__(self, column=t.Type[Column]):
        self.column = column

    def get_select_string(self, engine_type: str, just_alias=False) -> str:
        column_name = self.column._meta.get_full_name(just_alias=just_alias)
        return f"MAX({column_name}) AS max"


class Min(Selectable):
    """
    MIN() SQL function. The column type must be numeric to run the query.

    await Band.select(Min(Band.popularity)).run()
    """

    def __init__(self, column=t.Type[Column]):
        self.column = column

    def get_select_string(self, engine_type: str, just_alias=False) -> str:
        column_name = self.column._meta.get_full_name(just_alias=just_alias)
        return f"MIN({column_name}) AS min"


class Sum(Selectable):
    """
    SUM() SQL function. The column type must be numeric to run the query.

    await Band.select(Sum(Band.popularity)).run()
    """

    def __init__(self, column=t.Type[Column]):
        self.column = column

    def get_select_string(self, engine_type: str, just_alias=False) -> str:
        if self.column.column_type.split("(")[0] in NUMERIC_TYPES:
            column_name = self.column._meta.get_full_name(
                just_alias=just_alias
            )
        else:
            raise Exception(
                "The column type must be numeric to run the query."
            )
        return f"SUM({column_name}) AS sum"
