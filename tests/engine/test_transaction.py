import asyncio
import typing as t
from unittest import TestCase

from piccolo.engine.postgres import Atomic
from piccolo.engine.sqlite import SQLiteEngine, TransactionType
from piccolo.table import drop_db_tables_sync
from piccolo.utils.sync import run_sync
from tests.base import engines_only
from tests.example_apps.music.tables import Band, Manager


class TestAtomic(TestCase):
    def test_error(self):
        """
        Make sure queries in a transaction aren't committed if a query fails.
        """
        atomic = Band._meta.db.atomic()
        atomic.add(
            Manager.create_table(),
            Band.create_table(),
            Band.raw("MALFORMED QUERY ... SHOULD ERROR"),
        )
        try:
            atomic.run_sync()
        except Exception:
            pass
        self.assertTrue(not Band.table_exists().run_sync())
        self.assertTrue(not Manager.table_exists().run_sync())

    def test_succeeds(self):
        """
        Make sure that when atomic is run successfully the database is modified
        accordingly.
        """
        atomic = Band._meta.db.atomic()
        atomic.add(Manager.create_table(), Band.create_table())
        atomic.run_sync()

        self.assertTrue(Band.table_exists().run_sync())
        self.assertTrue(Manager.table_exists().run_sync())

        drop_db_tables_sync(Band, Manager)

    @engines_only("postgres", "cockroach")
    def test_pool(self):
        """
        Make sure atomic works correctly when a connection pool is active.
        """

        async def run():
            """
            We have to run this async function, so we can use a connection
            pool.
            """
            engine = Band._meta.db
            await engine.start_connection_pool()

            atomic: Atomic = engine.atomic()
            atomic.add(
                Manager.create_table(),
                Band.create_table(),
            )

            await atomic.run()
            await engine.close_connection_pool()

        run_sync(run())

        self.assertTrue(Band.table_exists().run_sync())
        self.assertTrue(Manager.table_exists().run_sync())

        drop_db_tables_sync(Band, Manager)


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

    @engines_only("postgres")
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
        self.assertEqual(len(set(txids)), 1)

        # Now run it again and make sure the transaction ids differ.
        next_txids = asyncio.run(run_transaction())
        self.assertNotEqual(txids, next_txids)


class TestTransactionExists(TestCase):
    def test_exists(self):
        """
        Make sure we can detect when code is within a transaction.
        """
        engine = t.cast(SQLiteEngine, Manager._meta.db)

        async def run_inside_transaction():
            async with engine.transaction():
                return engine.transaction_exists()

        self.assertTrue(asyncio.run(run_inside_transaction()))

        async def run_outside_transaction():
            return engine.transaction_exists()

        self.assertFalse(asyncio.run(run_outside_transaction()))


@engines_only("sqlite")
class TestTransactionType(TestCase):
    def setUp(self):
        Manager.create_table().run_sync()

    def tearDown(self):
        Manager.alter().drop_table().run_sync()

    def test_transaction(self):
        """
        With SQLite, we can specify the transaction type. This helps when
        we want to do concurrent writes, to avoid locking the database.

        https://github.com/piccolo-orm/piccolo/issues/687
        """
        engine = t.cast(SQLiteEngine, Manager._meta.db)

        async def run_transaction(name: str):
            async with engine.transaction(
                transaction_type=TransactionType.immediate
            ):
                # This does a SELECT followed by an INSERT, so is a good test.
                # If using TransactionType.deferred it would fail because
                # the database will become locked.
                await Manager.objects().get_or_create(Manager.name == name)

        manager_names = [f"Manager_{i}" for i in range(1, 10)]

        async def run_all():
            """
            Run all of the transactions concurrently.
            """
            await asyncio.gather(
                *[run_transaction(name=name) for name in manager_names]
            )

        asyncio.run(run_all())

        # Make sure it all ran effectively.
        self.assertListEqual(
            Manager.select(Manager.name)
            .order_by(Manager.name)
            .output(as_list=True)
            .run_sync(),
            manager_names,
        )

    def test_atomic(self):
        """
        Similar to above, but with ``Atomic``.
        """
        engine = t.cast(SQLiteEngine, Manager._meta.db)

        async def run_atomic(name: str):
            atomic = engine.atomic(transaction_type=TransactionType.immediate)
            atomic.add(Manager.objects().get_or_create(Manager.name == name))
            await atomic.run()

        manager_names = [f"Manager_{i}" for i in range(1, 10)]

        async def run_all():
            """
            Run all of the transactions concurrently.
            """
            await asyncio.gather(
                *[run_atomic(name=name) for name in manager_names]
            )

        asyncio.run(run_all())

        # Make sure it all ran effectively.
        self.assertListEqual(
            Manager.select(Manager.name)
            .order_by(Manager.name)
            .output(as_list=True)
            .run_sync(),
            manager_names,
        )
