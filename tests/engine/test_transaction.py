import asyncio
from unittest import TestCase

from piccolo.engine.sqlite import SQLiteEngine

from ..example_project.tables import Band, Manager
from ..base import postgres_only, sqlite_only


class TestAtomic(TestCase):
    def test_error(self):
        """
        Make sure queries in a transaction aren't committed if a query fails.
        """
        transaction = Band._meta.db.atomic()
        transaction.add(
            Manager.create_table(),
            Band.create_table(),
            Band.raw("MALFORMED QUERY ... SHOULD ERROR"),
        )
        try:
            transaction.run_sync()
        except Exception:
            pass
        self.assertTrue(not Band.table_exists().run_sync())
        self.assertTrue(not Manager.table_exists().run_sync())

    def test_succeeds(self):
        transaction = Band._meta.db.atomic()
        transaction.add(Manager.create_table(), Band.create_table())
        transaction.run_sync()

        self.assertTrue(Band.table_exists().run_sync())
        self.assertTrue(Manager.table_exists().run_sync())

        transaction.add(
            Band.alter().drop_table(), Manager.alter().drop_table()
        )
        transaction.run_sync()


class TestTransaction(TestCase):
    def tearDown(self):
        for table in (Band, Manager):
            if table.table_exists().run_sync():
                table.alter().drop_table().run_sync()

    def test_error(self):
        """
        Make sure queries in a transaction aren't committed if a query fails.
        """

        async def run_transaction():
            try:
                async with Band._meta.db.transaction():
                    Manager.create_table()
                    Band.create_table()
                    Band.raw("MALFORMED QUERY ... SHOULD ERROR")
            except Exception:
                pass

        asyncio.run(run_transaction())

        self.assertTrue(not Band.table_exists().run_sync())
        self.assertTrue(not Manager.table_exists().run_sync())

    def test_succeeds(self):
        async def run_transaction():
            async with Band._meta.db.transaction():
                await Manager.create_table().run()
                await Band.create_table().run()

        asyncio.run(run_transaction())

        self.assertTrue(Band.table_exists().run_sync())
        self.assertTrue(Manager.table_exists().run_sync())

    @postgres_only
    def test_transaction_id(self):
        """
        An extra sanity check, that the transaction id is the same for each
        query inside the transaction block.
        """

        async def run_transaction():
            responses = []
            async with Band._meta.db.transaction():
                responses.append(
                    await Manager.raw("SELECT txid_current()").run()
                )
                responses.append(
                    await Manager.raw("SELECT txid_current()").run()
                )
            return [i[0]["txid_current"] for i in responses]

        txids = asyncio.run(run_transaction())
        assert len(set(txids)) == 1

        # Now run it again and make sure the transaction ids differ.
        next_txids = asyncio.run(run_transaction())
        assert txids != next_txids
