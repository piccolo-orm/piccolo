import typing as t

from piccolo.columns.base import Column
from piccolo.querystring import QueryString


class Cast(QueryString):
    def __init__(
        self,
        identifier: t.Union[Column, QueryString],
        as_type: Column,
        alias: t.Optional[str] = None,
    ):
        """
        Cast a value to a different type. For example::

            >>> from piccolo.query.functions import Cast

            >>> await Concert.select(
            ...     Cast(Concert.starts, Time(), "start_time")
            ... )
            [{"start_time": datetime.time(19, 0)}]

        :param identifier:
            Identifies what is being converted (e.g. a column).
        :param as_type:
            The type to be converted to.

        """
        # Make sure the identifier is a supported type.

        if not isinstance(identifier, (Column, QueryString)):
            raise ValueError(
                "The identifier is an unsupported type - only Column and "
                "QueryString instances are allowed."
            )

        #######################################################################
        # Convert `as_type` to a string which can be used in the query.

        if not isinstance(as_type, Column):
            raise ValueError("The `as_type` value must be a Column instance.")

        # We need to give the column a reference to a table, and hence
        # the database engine, as the column type is sometimes dependent
        # on which database is being used.
        from piccolo.table import Table, create_table_class

        table: t.Optional[t.Type[Table]] = None

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

        #######################################################################

        super().__init__(
            f"CAST({{}} AS {as_type_string})",
            identifier,
            alias=alias,
        )


__all__ = ("Cast",)
