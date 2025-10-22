import uuid

from piccolo.columns.column_types import UUID
from piccolo.columns.defaults.uuid import UUID7
from piccolo.table import Table
from piccolo.testing.test_case import AsyncTableTest


class MyTable(Table):
    uuid = UUID()
    uuid_v7 = UUID(default=UUID7())


class TestUUID(AsyncTableTest):
    tables = [MyTable]

    async def test_return_type(self):
        row = MyTable()
        await row.save()

        self.assertIsInstance(row.uuid, uuid.UUID)
        self.assertIsInstance(row.uuid_v7, uuid.UUID)
