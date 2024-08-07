from piccolo.engine import engine_finder
from piccolo.testing.test_case import (
    AsyncTableTest,
    AsyncTransactionTest,
    TableTest,
)
from tests.example_apps.music.tables import Band, Manager


class TestTableTest(TableTest):

    tables = [Band, Manager]

    async def test_tables_created(self):
        self.assertTrue(Band.table_exists().run_sync())
        self.assertTrue(Manager.table_exists().run_sync())


class TestAsyncTableTest(AsyncTableTest):

    tables = [Band, Manager]

    async def test_tables_created(self):
        self.assertTrue(await Band.table_exists())
        self.assertTrue(await Manager.table_exists())


class TestAsyncTransaction(AsyncTransactionTest):

    async def test_transaction_exists(self):
        db = engine_finder()
        assert db is not None
        self.assertTrue(db.transaction_exists())
