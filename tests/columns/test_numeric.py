from decimal import Decimal
from unittest import TestCase

from piccolo.columns.column_types import Numeric
from piccolo.table import Table


class MyTable(Table):
    column_a = Numeric()
    column_b = Numeric(digits=(3, 2))


class TestNumeric(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_creation(self):
        row = MyTable(column_a=Decimal(1.23), column_b=Decimal(1.23))
        row.save().run_sync()

        _row = MyTable.objects().first().run_sync()

        self.assertTrue(type(_row.column_a) == Decimal)
        self.assertTrue(type(_row.column_b) == Decimal)

        self.assertAlmostEqual(_row.column_a, Decimal(1.23))
        self.assertEqual(_row.column_b, Decimal("1.23"))
