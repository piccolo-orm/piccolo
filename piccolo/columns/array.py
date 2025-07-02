from typing import Any, Union

from piccolo.columns.base import Column
from piccolo.querystring import QueryString


class ArrayCat(QueryString):
    def __init__(self, column: Column, value: Union[Any, list[Any]]):
        """
        Concatenate two arrays.

        :param column:
            Identifies the column.
        :param value:
            The value to concatenate.

        """
        engine_type = column._meta.engine_type
        if engine_type not in ("postgres", "cockroach"):
            raise ValueError(
                "Only Postgres and Cockroach support array concatenating."
            )

        if not isinstance(value, list):
            value = [value]

        super().__init__(
            f'array_cat("{column._meta.db_column_name}", {{}})',
            value,
        )


class ArrayAppend(QueryString):
    def __init__(self, column: Column, value: Any):
        """
        Append an element to the end of an array.

        :param column:
            Identifies the column.
        :param value:
            The value to append.

        """
        engine_type = column._meta.engine_type
        if engine_type not in ("postgres", "cockroach"):
            raise ValueError(
                "Only Postgres and Cockroach support array appending."
            )

        super().__init__(
            f'array_append("{column._meta.db_column_name}", {{}})',
            value,
        )


class ArrayPrepend(QueryString):
    def __init__(self, column: Column, value: Any):
        """
        Append an element to the beginning of an array.

        :param value:
            The value to prepend.
        :param column:
            Identifies the column.

        """
        engine_type = column._meta.engine_type
        if engine_type not in ("postgres", "cockroach"):
            raise ValueError(
                "Only Postgres and Cockroach support array prepending."
            )

        super().__init__(
            f'array_prepend({{}}, "{column._meta.db_column_name}")',
            value,
        )


class ArrayReplace(QueryString):
    def __init__(self, column: Column, old_value: Any, new_value: Any):
        """
        Replace each array element equal to the given value with a new value.

        :param column:
            Identifies the column.
        :param old_value:
            The old value to be replaced.
        :param new_value:
            The new value we are replacing with.

        """
        engine_type = column._meta.engine_type
        if engine_type not in ("postgres", "cockroach"):
            raise ValueError(
                "Only Postgres and Cockroach support array substitution."
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

        :param column:
            Identifies the column.
        :param value:
            The value to remove.

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
    "ArrayCat",
    "ArrayAppend",
    "ArrayPrepend",
    "ArrayReplace",
    "ArrayRemove",
)
