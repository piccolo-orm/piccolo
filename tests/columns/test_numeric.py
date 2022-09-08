from decimal import Decimal
from unittest import TestCase

from piccolo.columns.column_types import Numeric
from piccolo.table import Table

from tests.base import engine_is

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

        self.assertEqual(type(_row.column_a), Decimal)
        self.assertEqual(type(_row.column_b), Decimal)

        self.assertAlmostEqual(_row.column_a, Decimal(1.23))
        if not engine_is('cockroach'): # Cockroach returns "1.22999999999999998223643160...."
            self.assertEqual(_row.column_b, Decimal("1.23"))
