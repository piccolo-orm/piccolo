from typing import TYPE_CHECKING, Any, Union

from typing_extensions import TypeAlias, TypeGuard

if TYPE_CHECKING:
    from piccolo.columns.base import Column
    from piccolo.querystring import QueryString

    ArrayType: TypeAlias = Union[Column, QueryString, list[Any]]


def is_array_type(value) -> TypeGuard[ArrayType]:
    from piccolo.columns.base import Column
    from piccolo.querystring import QueryString

    return isinstance(value, QueryString) or isinstance(value, Column)


class ArrayMethodsMixin:

    def cat(self, array: ArrayType):
        """
        Used in an ``update`` query to concatenate two arrays.

        .. code-block:: python

            >>> await Ticket.update({
            ...     Ticket.seat_numbers: Ticket.seat_numbers.cat([1000])
            ... }).where(Ticket.id == 1)

        You can also use the ``+`` symbol if you prefer. To concatenate to
        the end:

        .. code-block:: python

            >>> await Ticket.update({
            ...     Ticket.seat_numbers: Ticket.seat_numbers + [1000]
            ... }).where(Ticket.id == 1)

        To concatenate to the start:

        .. code-block:: python

            >>> await Ticket.update({
            ...     Ticket.seat_numbers: [1000] + Ticket.seat_numbers
            ... }).where(Ticket.id == 1)

        You can concatenate multiple arrays in one go:

        .. code-block:: python

            >>> await Ticket.update({
            ...     Ticket.seat_numbers: [1000] + Ticket.seat_numbers + [2000]
            ... }).where(Ticket.id == 1)

        .. note:: Postgres / CockroachDB only

        """
        assert is_array_type(self)
        return ArrayCat(array_1=self, array_2=array)

    def __add__(self, array: ArrayType):
        """
        QueryString will use the ``+`` operator by default for addition, but
        for arrays we want to concatenate them instead.
        """
        assert is_array_type(self)
        return ArrayCat(array_1=self, array_2=array)

    def __radd__(self, array: ArrayType):
        assert is_array_type(self)
        return ArrayCat(array_1=array, array_2=self)

    def remove(self, value: Any):
        """
        Used in an ``update`` query to remove an item from an array.

        .. code-block:: python

            >>> await Ticket.update({
            ...     Ticket.seat_numbers: Ticket.seat_numbers.remove(1000)
            ... }).where(Ticket.id == 1)

        .. note:: Postgres / CockroachDB only

        """
        assert is_array_type(self)
        return ArrayRemove(array=self, value=value)

    def replace(self, old_value: Any, new_value: Any):
        """
        Used in an ``update`` query to replace each array item
        equal to the given value with a new value.

        .. code-block:: python

            >>> await Ticket.update({
            ...     Ticket.seat_numbers: Ticket.seat_numbers.replace(1000, 500)
            ... }).where(Ticket.id == 1)

        .. note:: Postgres / CockroachDB only

        """
        assert is_array_type(self)
        return ArrayReplace(
            array=self, old_value=old_value, new_value=new_value
        )

    def append(self, value: Any):
        """
        Used in an ``update`` query to append an item to an array.

        .. code-block:: python

            >>> await Ticket.update({
            ...     Ticket.seat_numbers: Ticket.seat_numbers.append(1000)
            ... }).where(Ticket.id == 1)

        .. note:: Postgres / CockroachDB only

        """
        assert is_array_type(self)
        return ArrayAppend(array=self, value=value)

    def prepend(self, value: Any):
        """
        Used in an ``update`` query to prepend an item to an array.

        .. code-block:: python

            >>> await Ticket.update({
            ...     Ticket.seat_numbers: Ticket.seat_numbers.prepend(1000)
            ... }).where(Ticket.id == 1)

        .. note:: Postgres / CockroachDB only

        """
        assert is_array_type(self)
        return ArrayPrepend(array=self, value=value)


class ArrayQueryString(QueryString, ArrayMethodsMixin):
    pass


def validate_engine(value):
    from piccolo.columns.base import Column

    if isinstance(value, Column):
        engine_type = value._meta.engine_type
        if engine_type not in ("postgres", "cockroach"):
            raise ValueError(
                "Only Postgres and CockroachDB support this feature."
            )


class ArrayCat(ArrayQueryString):
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
            validate_engine(value)

        super().__init__("array_cat({}, {})", array_1, array_2)


class ArrayAppend(ArrayQueryString):
    def __init__(self, array: ArrayType, value: Any):
        """
        Append an element to the end of an array.

        :param array:
            Identifies the array.
        :param value:
            The value to append.

        """
        validate_engine(array)

        super().__init__("array_append({}, {})", array, value)


class ArrayPrepend(ArrayQueryString):
    def __init__(self, array: ArrayType, value: Any):
        """
        Append an element to the beginning of an array.

        :param array:
            Identifies the array.
        :param column:
            The value to prepend.

        """
        validate_engine(value)

        super().__init__("array_prepend({}, {})", value, array)


class ArrayReplace(ArrayQueryString):
    def __init__(self, array: ArrayType, old_value: Any, new_value: Any):
        """
        Replace each array element equal to the given value with a new value.

        :param array:
            Identifies the array.
        :param old_value:
            The old value to be replaced.
        :param new_value:
            The new value we are replacing with.

        """
        validate_engine(array)

        super().__init__(
            "array_replace({}, {}, {})", array, old_value, new_value
        )


class ArrayRemove(ArrayQueryString):
    def __init__(self, array: ArrayType, value: Any):
        """
        Remove all elements equal to the given value
        from the array (array must be one-dimensional).

        :param array:
            Identifies the array.
        :param value:
            The value to remove.

        """
        validate_engine(array)

        super().__init__("array_remove({}, {})", array, value)


__all__ = (
    "ArrayCat",
    "ArrayAppend",
    "ArrayPrepend",
    "ArrayReplace",
    "ArrayRemove",
)
