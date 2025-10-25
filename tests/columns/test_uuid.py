import uuid

from piccolo.columns.column_types import UUID
from piccolo.columns.defaults.uuid import UUID7
from piccolo.table import Table
from piccolo.testing.test_case import AsyncTableTest
from tests.base import postgres_only


class UUIDTable(Table):
    uuid = UUID()


class TestUUID(AsyncTableTest):
    tables = [UUIDTable]

    async def test_return_type(self):
        row = UUIDTable()
        await row.save()

        self.assertIsInstance(row.uuid, uuid.UUID)


class UUID7Table(Table):
    uuid_7 = UUID(default=UUID7())


@postgres_only
class TestUUID7(AsyncTableTest):
    tables = [UUID7Table]

    async def test_return_type(self):
        row = UUID7Table()
        await row.save()

        self.assertIsInstance(row.uuid_7, uuid.UUID)
