from unittest import TestCase
import uuid

from piccolo.table import Table
from piccolo.columns.column_types import UUID


class MyTable(Table):
    uuid = UUID()


class TestUUID(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_return_type(self):
        row = MyTable()
        row.save().run_sync()

        self.assertIsInstance(row.uuid, uuid.UUID)
