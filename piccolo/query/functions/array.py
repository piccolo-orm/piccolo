from typing import Any, Union

from typing_extensions import TypeAlias

from piccolo.columns.base import Column
from piccolo.querystring import QueryString

ArrayType: TypeAlias = Union[Column, QueryString, list[Any]]


class ArrayCat(QueryString):
    def __init__(
        self,
        array_1: ArrayType,
        array_2: ArrayType,
    ):
        """
        Concatenate two arrays.

        :param array_1:
            These values will be at the start of the new array.
        :param array_2:
            These values will be at the end of the new array.

        """
        for value in (array_1, array_2):
            if isinstance(value, Column):
                engine_type = value._meta.engine_type
                if engine_type not in ("postgres", "cockroach"):
                    raise ValueError(
                        "Only Postgres and Cockroach support array "
                        "concatenation."
                    )

        super().__init__("array_cat({}, {})", array_1, array_2)


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
