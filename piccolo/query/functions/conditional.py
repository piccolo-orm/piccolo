from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from piccolo.custom_types import BasicTypes
from piccolo.querystring import QueryString

if TYPE_CHECKING:
    from piccolo.columns import Column


class Coalesce(QueryString):
    def __init__(
        self,
        *args: Union[Column, QueryString, BasicTypes],
        alias: Optional[str] = None,
    ):
        """
        Returns the first non-null value.

        Here's an example to try in the playground::

            >>> await Album.select(Album.release_date)
            [
                {'release_date': datetime.date(2021, 1, 1)},
                {'release_date': datetime.date(2025, 1, 1)},
                {'release_date': datetime.date(2022, 2, 2)},
                {'release_date': None}
            ]

        One of the values is null - we can specify a fallback value::

            >>> from piccolo.functions.conditional import Coalesce
            >>> await Album.select(
            ...     Coalesce(Album.release_date, datetime.date(2050, 1, 1))
            ... )
            [
                {'release_date': datetime.date(2021, 1, 1)},
                {'release_date': datetime.date(2025, 1, 1)},
                {'release_date': datetime.date(2022, 2, 2)},
                {'release_date': datetime.date(2050, 1, 1)}
            ]

        Or us this abbreviated syntax::

            >>> await Album.select(
            ...     Album.release_date | datetime.date(2050, 1, 1)
            ... )
            [
                {'release_date': datetime.date(2021, 1, 1)},
                {'release_date': datetime.date(2025, 1, 1)},
                {'release_date': datetime.date(2022, 2, 2)},
                {'release_date': datetime.date(2050, 1, 1)}
            ]

        """
        if len(args) < 2:
            raise ValueError("At least two values must be passed in.")

        #######################################################################
        # Preserve the original alias from the column.

        from piccolo.columns import Column

        first_arg = args[0]

        if isinstance(first_arg, Column):
            alias = (
                alias
                or first_arg._alias
                or first_arg._meta.get_default_alias()
            )
        elif isinstance(first_arg, QueryString):
            alias = alias or first_arg._alias

        #######################################################################

        placeholders = ", ".join("{}" for _ in args)

        super().__init__(f"COALESCE({placeholders})", *args, alias=alias)


class NullIf(QueryString):
    def __init__(
        self,
        identifier: Union[Column, QueryString],
        value: Union[BasicTypes, QueryString],
        alias: Optional[str] = None,
    ):
        """
        Returns null if the value in the database equals ``value``.

        An example is where a ``Varchar`` or ``Text`` column contains a mix of
        empty strings and null. We might want to standardise the response so
        it's just null.

        For example::

            class Venue(Table):
                name = Varchar()
                address = Text(default=None, null=True)

            >>> await Venue.select(Venue.name, NullIf(Venue.address, ''))
            [{'name': 'Amazing venue', 'address': None}]

        """
        # Preserve the original alias from the column.

        from piccolo.columns import Column

        if isinstance(identifier, Column):
            alias = (
                alias
                or identifier._alias
                or identifier._meta.get_default_alias()
            )
        elif isinstance(identifier, QueryString):
            alias = alias or identifier._alias

        #######################################################################

        super().__init__("NULLIF({}, {})", identifier, value, alias=alias)
