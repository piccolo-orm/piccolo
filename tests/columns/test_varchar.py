from unittest import TestCase

from piccolo.table import Table
from piccolo.columns.column_types import Varchar


class MyTable(Table):
    name = Varchar(length=10)


class TestVarchar(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_length(self):
        row = MyTable(name="bob")
        row.save().run_sync()

        with self.assertRaises(Exception):
            row.name = "bob123456789"
            row.save().run_sync()
