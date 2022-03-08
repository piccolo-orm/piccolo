from unittest import TestCase

from piccolo.columns.column_types import Integer, Varchar
from piccolo.table import Table


class Concert(Table):
    """
    ``order`` is a problematic name, as it clashes with a reserved SQL keyword:

    https://www.postgresql.org/docs/current/sql-keywords-appendix.html

    """

    name = Varchar()
    order = Integer()


class TestReservedColumnNames(TestCase):
    """
    Make sure the table works as expected, even though it has a problematic
    column name.
    """

    def setUp(self):
        Concert.create_table().run_sync()

    def tearDown(self):
        Concert.alter().drop_table().run_sync()

    def test_common_operations(self):
        # Save / Insert
        concert = Concert(name="Royal Albert Hall", order=1)
        concert.save().run_sync()
        self.assertEqual(
            Concert.select(Concert.order).run_sync(),
            [{"order": 1}],
        )

        # Save / Update
        concert.order = 2
        concert.save().run_sync()
        self.assertEqual(
            Concert.select(Concert.order).run_sync(),
            [{"order": 2}],
        )

        # Update
        Concert.update({Concert.order: 3}, force=True).run_sync()
        self.assertEqual(
            Concert.select(Concert.order).run_sync(),
            [{"order": 3}],
        )

        # Delete
        Concert.delete().where(Concert.order == 3).run_sync()
        self.assertEqual(
            Concert.select(Concert.order).run_sync(),
            [],
        )
