import sys

import pytest

from piccolo.engine import engine_finder
from piccolo.testing.test_case import (
    AsyncTableTest,
    AsyncTransactionTest,
    TableTest,
)
from tests.example_apps.music.tables import Band, Manager


class TestTableTest(TableTest):
    """
    Make sure the tables are created automatically.
    """

    tables = [Band, Manager]

    async def test_tables_created(self):
        self.assertTrue(Band.table_exists().run_sync())
        self.assertTrue(Manager.table_exists().run_sync())


class TestAsyncTableTest(AsyncTableTest):
    """
    Make sure the tables are created automatically in async tests.
    """

    tables = [Band, Manager]

    async def test_tables_created(self):
        self.assertTrue(await Band.table_exists())
        self.assertTrue(await Manager.table_exists())


@pytest.mark.skipif(sys.version_info <= (3, 11), reason="Python 3.11 required")
class TestAsyncTransaction(AsyncTransactionTest):
    """
    Make sure that the test exists within a transaction.
    """

    async def test_transaction_exists(self):
        db = engine_finder()
        assert db is not None
        self.assertTrue(db.transaction_exists())


@pytest.mark.skipif(sys.version_info <= (3, 11), reason="Python 3.11 required")
class TestAsyncTransactionRolledBack(AsyncTransactionTest):
    """
    Make sure that the changes get rolled back automatically.
    """

    async def asyncTearDown(self):
        await super().asyncTearDown()

        assert Manager.table_exists().run_sync() is False

    async def test_insert_data(self):
        await Manager.create_table()

        manager = Manager({Manager.name: "Guido"})
        await manager.save()
