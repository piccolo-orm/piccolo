from unittest import TestCase

from piccolo.table import Table
from piccolo.columns.column_types import UUID


class MyTable(Table):
    uuid = UUID()


class TestVarchar(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_creation(self):
        row = MyTable()
        row.save().run_sync()

        self.assertEqual(len(row.uuid), 36)
