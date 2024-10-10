import typing as t

from piccolo.columns.base import Column
from piccolo.querystring import QueryString

from .base import Function


class Avg(Function):
    """
    ``AVG()`` SQL function. Column type must be numeric to run the query.

    .. code-block:: python

        await Band.select(Avg(Band.popularity))

        # We can use an alias. These two are equivalent:

        await Band.select(
            Avg(Band.popularity, alias="popularity_avg")
        )

        await Band.select(
            Avg(Band.popularity).as_alias("popularity_avg")
        )

    """

    function_name = "AVG"


class Count(QueryString):
    """
    Used in ``Select`` queries, usually in conjunction with the ``group_by``
    clause::

        >>> await Band.select(
        ...     Band.manager.name.as_alias('manager_name'),
        ...     Count(alias='band_count')
        ... ).group_by(Band.manager)
        [{'manager_name': 'Guido', 'count': 1}, ...]

    It can also be used without the ``group_by`` clause (though you may prefer
    to the :meth:`Table.count <piccolo.table.Table.count>` method instead, as
    it's more convenient)::

        >>> await Band.select(Count())
        [{'count': 3}]

    """

    def __init__(
        self,
        column: t.Optional[Column] = None,
        distinct: t.Optional[t.Sequence[Column]] = None,
        alias: str = "count",
    ):
        """
        :param column:
            If specified, the count is for non-null values in that column.
        :param distinct:
            If specified, the count is for distinct values in those columns.
        :param alias:
            The name of the value in the response::

                # These two are equivalent:

                await Band.select(
                    Band.name, Count(alias="total")
                ).group_by(Band.name)

                await Band.select(
                    Band.name,
                    Count().as_alias("total")
                ).group_by(Band.name)

        """
        if distinct and column:
            raise ValueError("Only specify `column` or `distinct`")

        if distinct:
            engine_type = distinct[0]._meta.engine_type
            if engine_type == "sqlite":
                # SQLite doesn't allow us to specify multiple columns, so
                # instead we concatenate the values.
                column_names = " || ".join("{}" for _ in distinct)
            else:
                column_names = ", ".join("{}" for _ in distinct)

            return super().__init__(
                f"COUNT(DISTINCT({column_names}))", *distinct, alias=alias
            )
        else:
            if column:
                return super().__init__("COUNT({})", column, alias=alias)
            else:
                return super().__init__("COUNT(*)", alias=alias)


class Min(Function):
    """
    ``MIN()`` SQL function.

    .. code-block:: python

        await Band.select(Min(Band.popularity))

        # We can use an alias. These two are equivalent:

        await Band.select(
            Min(Band.popularity, alias="popularity_min")
        )

        await Band.select(
            Min(Band.popularity).as_alias("popularity_min")
        )

    """

    function_name = "MIN"


class Max(Function):
    """
    ``MAX()`` SQL function.

    .. code-block:: python

        await Band.select(
            Max(Band.popularity)
        )

        # We can use an alias. These two are equivalent:

        await Band.select(
            Max(Band.popularity, alias="popularity_max")
        )

        await Band.select(
            Max(Band.popularity).as_alias("popularity_max")
        )

    """

    function_name = "MAX"


class Sum(Function):
    """
    ``SUM()`` SQL function. Column type must be numeric to run the query.

    .. code-block:: python

        await Band.select(
            Sum(Band.popularity)
        )

        # We can use an alias. These two are equivalent:

        await Band.select(
            Sum(Band.popularity, alias="popularity_sum")
        )

        await Band.select(
            Sum(Band.popularity).as_alias("popularity_sum")
        )

    """

    function_name = "SUM"


__all__ = (
    "Avg",
    "Count",
    "Min",
    "Max",
    "Sum",
)
