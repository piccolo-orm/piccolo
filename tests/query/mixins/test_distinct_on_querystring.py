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

    def test_querystring_as_first_order_by_should_raise(self):
        """
        A QueryString as the first order_by column must raise
        DistinctOnError, since it can never match a Column passed to
        distinct(on=...).
        """
        order_by = OrderBy(
            order_by_items=[
                OrderByItem(
                    columns=[QueryString("random()")], ascending=True
                )
            ]
        )
        with self.assertRaises(DistinctOnError):
            self._distinct_on_band().validate_on(order_by)

    def test_orderbyraw_as_first_order_by_should_raise(self):
        """
        An OrderByRaw as the first order_by column must raise
        DistinctOnError, since it can never match a Column passed to
        distinct(on=...).
        """
        order_by = OrderBy(
            order_by_items=[
                OrderByItem(
                    columns=[OrderByRaw("random()")], ascending=True
                )
            ]
        )
        with self.assertRaises(DistinctOnError):
            self._distinct_on_band().validate_on(order_by)

    def test_mismatched_column_still_raises(self):
        """
        A Column that doesn't match the distinct on column must still
        raise DistinctOnError.
        """
        order_by = OrderBy(
            order_by_items=[
                OrderByItem(columns=[Album.title], ascending=True)
            ]
        )
        with self.assertRaises(DistinctOnError):
            self._distinct_on_band().validate_on(order_by)

    def test_matching_column_does_not_raise(self):
        """
        A Column matching the distinct on column must not raise.
        """
        order_by = OrderBy(
            order_by_items=[
                OrderByItem(columns=[Album.band], ascending=True)
            ]
        )
        self._distinct_on_band().validate_on(order_by)
