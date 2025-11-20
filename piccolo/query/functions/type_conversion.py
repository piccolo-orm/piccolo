from __future__ import annotations

from typing import Optional, Union

from piccolo.columns.base import Column
from piccolo.custom_types import BasicTypes
from piccolo.querystring import QueryString


class Cast(QueryString):
    def __init__(
        self,
        identifier: Union[Column, QueryString, BasicTypes],
        as_type: Column,
        alias: Optional[str] = None,
    ):
        """
        Cast a value to a different type. For example::

            >>> from piccolo.query.functions import Cast

            >>> await Concert.select(
            ...     Cast(Concert.starts, Time(), alias="start_time")
            ... )
            [{"start_time": datetime.time(19, 0)}]

        You may also need ``Cast`` to explicitly tell the database which type
        you're sending in the query (though this is an edge case). Here is a
        contrived example::

            >>> from piccolo.query.functions.math import Count

            # This fails with asyncpg:
            >>> await Band.select(Count([1,2,3]))

        If we explicitly specify the type of the array, then it works::

            >>> await Band.select(
            ...     Count(
            ...         Cast(
            ...             [1,2,3],
            ...             Array(Integer())
            ...         ),
            ...     )
            ... )

        :param identifier:
            Identifies what is being converted (e.g. a column, or a raw value).
        :param as_type:
            The type to be converted to.

        """
        # Convert `as_type` to a string which can be used in the query.

        if not isinstance(as_type, Column):
            raise ValueError("The `as_type` value must be a Column instance.")

        # We need to give the column a reference to a table, and hence
        # the database engine, as the column type is sometimes dependent
        # on which database is being used.

        from piccolo.table import Table, create_table_class

        table: Optional[type[Table]] = None

        if isinstance(identifier, Column):
            table = identifier._meta.table
        elif isinstance(identifier, QueryString):
            table = (
                identifier.columns[0]._meta.table
                if identifier.columns
                else None
            )

        as_type._meta.table = table or create_table_class("Table")
        as_type_string = as_type.column_type

        #######################################################################
        # Preserve the original alias from the column.

        if isinstance(identifier, Column):
            alias = (
                alias
                or identifier._alias
                or identifier._meta.get_default_alias()
            )

        # for MySQL we need to change as_type_string
        if as_type._meta.table._meta.db.engine_type == "mysql":
            if as_type_string == "INTEGER":
                as_type_string = "SIGNED"
            else:
                as_type_string = "CHAR"

        #######################################################################

        super().__init__(
            f"CAST({{}} AS {as_type_string})",
            identifier,
            alias=alias,
        )


__all__ = ("Cast",)
