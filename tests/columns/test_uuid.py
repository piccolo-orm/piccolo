import uuid

from piccolo.columns.column_types import UUID
from piccolo.table import Table
from piccolo.testing.test_case import TableTest


class MyTable(Table):
    uuid = UUID()


class TestUUID(TableTest):
    tables = [MyTable]

    def test_return_type(self):
        row = MyTable()
        row.save().run_sync()

        self.assertIsInstance(row.uuid, uuid.UUID)
