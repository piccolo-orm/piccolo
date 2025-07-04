from typing import Any, Union

from piccolo.columns.base import Column
from piccolo.querystring import QueryString


class ArrayCat(QueryString):
    def __init__(
        self, column: Union[Column, QueryString], value: Union[Any, list[Any]]
    ):
        """
        Concatenate two arrays.

        :param column:
            Identifies the column.
        :param value:
            The value to concatenate.

        """
        if isinstance(column, Column):
            engine_type = column._meta.engine_type
            if engine_type not in ("postgres", "cockroach"):
                raise ValueError(
                    "Only Postgres and Cockroach support array concatenating."
                )

        if not isinstance(value, list):
            value = [value]

        super().__init__("array_cat({}, {})", column, value)


class ArrayAppend(QueryString):
    def __init__(self, column: Union[Column, QueryString], value: Any):
        """
        Append an element to the end of an array.

        :param column:
            Identifies the column.
        :param value:
            The value to append.

        """
        if isinstance(column, Column):
            engine_type = column._meta.engine_type
            if engine_type not in ("postgres", "cockroach"):
                raise ValueError(
                    "Only Postgres and Cockroach support array appending."
                )

        super().__init__("array_append({}, {})", column, value)


class ArrayPrepend(QueryString):
    def __init__(self, column: Union[Column, QueryString], value: Any):
        """
        Append an element to the beginning of an array.

        :param value:
            The value to prepend.
        :param column:
            Identifies the column.

        """
        if isinstance(column, Column):
            engine_type = column._meta.engine_type
            if engine_type not in ("postgres", "cockroach"):
                raise ValueError(
                    "Only Postgres and Cockroach support array prepending."
                )

        super().__init__("array_prepend({}, {})", value, column)


class ArrayReplace(QueryString):
    def __init__(
        self,
        column: Union[Column, QueryString],
        old_value: Any,
        new_value: Any,
    ):
        """
        Replace each array element equal to the given value with a new value.

        :param column:
            Identifies the column.
        :param old_value:
            The old value to be replaced.
        :param new_value:
            The new value we are replacing with.

        """
        if isinstance(column, Column):
            engine_type = column._meta.engine_type
            if engine_type not in ("postgres", "cockroach"):
                raise ValueError(
                    "Only Postgres and Cockroach support array substitution."
                )

        super().__init__(
            "array_replace({}, {}, {})", column, old_value, new_value
        )


class ArrayRemove(QueryString):
    def __init__(self, column: Union[Column, QueryString], value: Any):
        """
        Remove all elements equal to the given value
        from the array (array must be one-dimensional).

        :param column:
            Identifies the column.
        :param value:
            The value to remove.

        """
        if isinstance(column, Column):
            engine_type = column._meta.engine_type
            if engine_type not in ("postgres", "cockroach"):
                raise ValueError(
                    "Only Postgres and Cockroach support array removing."
                )

        super().__init__("array_remove({}, {})", column, value)


__all__ = (
    "ArrayCat",
    "ArrayAppend",
    "ArrayPrepend",
    "ArrayReplace",
    "ArrayRemove",
)
