from unittest import TestCase

from piccolo.columns.column_types import Varchar
from piccolo.query.mixins import (
    Distinct,
    DistinctOnError,
    OrderBy,
    OrderByItem,
    OrderByRaw,
)
from piccolo.querystring import QueryString
from piccolo.table import Table


class Album(Table):
    band = Varchar()
    title = Varchar()


class TestDistinctValidateOn(TestCase):

    def _distinct_on_band(self) -> Distinct:
        return Distinct(enabled=True, on=[Album.band])

    def test_querystring_as_first_order_by_is_allowed(self):
        """
        A QueryString as the first order_by column isn't rejected, as it can
        match the column passed to distinct(on=...). For example
        ``QueryString("{}", Album.band)`` compiles to the same expression.
        Postgres reports a genuine mismatch itself.
        """
        order_by = OrderBy(
            order_by_items=[
                OrderByItem(
                    columns=[QueryString("{}", Album.band)], ascending=True
                )
            ]
        )
        self._distinct_on_band().validate_on(order_by)

    def test_orderbyraw_as_first_order_by_is_allowed(self):
        """
        Same as above, but using ``OrderByRaw``, which existing code relies
        on.
        """
        order_by = OrderBy(
            order_by_items=[
                OrderByItem(
                    columns=[OrderByRaw('"album"."band"')], ascending=True
                )
            ]
        )
        self._distinct_on_band().validate_on(order_by)

    def test_mismatched_column_still_raises(self):
        """
        A Column that doesn't match the distinct on column must still
        raise DistinctOnError.
        """
        order_by = OrderBy(
            order_by_items=[OrderByItem(columns=[Album.title], ascending=True)]
        )
        with self.assertRaises(DistinctOnError):
            self._distinct_on_band().validate_on(order_by)

    def test_matching_column_does_not_raise(self):
        """
        A Column matching the distinct on column must not raise.
        """
        order_by = OrderBy(
            order_by_items=[OrderByItem(columns=[Album.band], ascending=True)]
        )
        self._distinct_on_band().validate_on(order_by)
