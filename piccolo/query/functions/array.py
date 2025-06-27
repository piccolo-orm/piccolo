from typing import Any

from piccolo.columns.base import Column
from piccolo.querystring import QueryString


class ArrayAppend(QueryString):
    def __init__(self, column: Column, value: Any):
        """
        Append an element to the end of an array.

        :param columns:
            Identifies the column.
        :param value:
            The value to append.

        .. code-block:: python

            >>> await Ticket.update({
            ...     Ticket.seat_numbers: ArrayAppend(Ticket.seat_numbers, 10)
            ... }).where(Ticket.id == 1)

        """
        engine_type = column._meta.engine_type
        if engine_type not in ("postgres", "cockroach"):
            raise ValueError(
                "Only Postgres and Cockroach support array removing."
            )

        super().__init__(
            f'array_append("{column._meta.db_column_name}", {{}})',
            value,
        )


class ArrayPrepend(QueryString):
    def __init__(self, value: Any, column: Column):
        """
        Append an element to the beginning of an array.

        :param value:
            The value to prepend.
        :param columns:
            Identifies the column.

        .. code-block:: python

            >>> await Ticket.update({
            ...     Ticket.seat_numbers: ArrayPrepend(10, Ticket.seat_numbers)
            ... }).where(Ticket.id == 1)

        """
        engine_type = column._meta.engine_type
        if engine_type not in ("postgres", "cockroach"):
            raise ValueError(
                "Only Postgres and Cockroach support array removing."
            )

        super().__init__(
            f'array_prepend({{}}, "{column._meta.db_column_name}")',
            value,
        )


class ArrayReplace(QueryString):
    def __init__(self, column: Column, old_value: Any, new_value: Any):
        """
        Replace each array element equal to the given value with a new value.

        :param columns:
            Identifies the column.
        :param old_value:
            The old value to be replaced.
        :param new_value:
            The new value we are replacing with.

        .. code-block:: python

            >>> await Ticket.update({
            ...     Ticket.seat_numbers: ArrayReplace(Ticket.seat_numbers, 10, 5)
            ... }).where(Ticket.id == 1)

        """  # noqa: E501
        engine_type = column._meta.engine_type
        if engine_type not in ("postgres", "cockroach"):
            raise ValueError(
                "Only Postgres and Cockroach support array removing."
            )

        super().__init__(
            f'array_replace("{column._meta.db_column_name}", {{}}, {{}})',
            old_value,
            new_value,
        )


class ArrayRemove(QueryString):
    def __init__(self, column: Column, value: Any):
        """
        Remove all elements equal to the given value
        from the array (array must be one-dimensional).

        :param columns:
            Identifies the column.
        :param value:
            The value to remove.

        .. code-block:: python

            >>> await Ticket.update({
            ...     Ticket.seat_numbers: ArrayRemove(Ticket.seat_numbers, 10)
            ... }).where(Ticket.id == 1)

        """
        engine_type = column._meta.engine_type
        if engine_type not in ("postgres", "cockroach"):
            raise ValueError(
                "Only Postgres and Cockroach support array removing."
            )

        super().__init__(
            f'array_remove("{column._meta.db_column_name}", {{}})',
            value,
        )


__all__ = (
    "ArrayAppend",
    "ArrayPrepend",
    "ArrayReplace",
    "ArrayRemove",
)
