import os
from unittest import TestCase

from piccolo.columns.column_types import SmallInt
from piccolo.table import Table

from ..base import engines_only


class MyTable(Table):
    value = SmallInt()


@engines_only("postgres", "cockroach")
class TestSmallIntPostgres(TestCase):
    """
    Make sure a SmallInt column in Postgres can only store small numbers.
    """

    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def _test_length(self):
        # Can store 2 bytes, but split between positive and negative values.
        max_value = int(2**16 / 2) - 1
        min_value = max_value * -1

        print("Testing max value")
        row = MyTable(value=max_value)
        row.save().run_sync()

        print("Testing min value")
        row.value = min_value
        row.save().run_sync()

        if "TRAVIS" not in os.environ:
            # This stalls out on Travis - not sure why.
            with self.assertRaises(Exception):
                row.value = max_value + 100
                row.save().run_sync()
