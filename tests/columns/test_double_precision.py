from unittest import TestCase

from piccolo.columns.column_types import DoublePrecision
from piccolo.table import Table


class MyTable(Table):
    column_a = DoublePrecision()


class TestDoublePrecision(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_creation(self):
        row = MyTable(column_a=1.23)
        row.save().run_sync()

        _row = MyTable.objects().first().run_sync()
        self.assertTrue(type(_row.column_a) == float)
        self.assertAlmostEqual(_row.column_a, 1.23)
