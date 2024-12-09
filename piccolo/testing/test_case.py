from __future__ import annotations

import typing as t
from unittest import IsolatedAsyncioTestCase, TestCase

from piccolo.engine import Engine, engine_finder
from piccolo.table import (
    Table,
    create_db_tables,
    create_db_tables_sync,
    drop_db_tables,
    drop_db_tables_sync,
)


class TableTest(TestCase):
    """
    Identical to :class:`AsyncTableTest <piccolo.testing.test_case.AsyncTableTest>`,
    except it only work for sync tests. Only use this if you can't make your
    tests async (perhaps you're on Python 3.7 where ``IsolatedAsyncioTestCase``
    isn't available).

    For example::

        class TestBand(TableTest):
            tables = [Band]

            def test_band(self):
                ...

    """  # noqa: E501

    tables: t.List[t.Type[Table]]

    def setUp(self) -> None:
        create_db_tables_sync(*self.tables)

    def tearDown(self) -> None:
        drop_db_tables_sync(*self.tables)


class AsyncTableTest(IsolatedAsyncioTestCase):
    """
    Used for tests where we need to create Piccolo tables - they will
    automatically be created and dropped.

    For example::

        class TestBand(AsyncTableTest):
            tables = [Band]

            async def test_band(self):
                ...

    """

    tables: t.List[t.Type[Table]]

    async def asyncSetUp(self) -> None:
        await create_db_tables(*self.tables)

    async def asyncTearDown(self) -> None:
        await drop_db_tables(*self.tables)


class AsyncTransactionTest(IsolatedAsyncioTestCase):
    """
    Wraps each test in a transaction, which is automatically rolled back when
    the test finishes.

    .. warning::
        Python 3.11 and above only.

    If your test suite just contains ``AsyncTransactionTest`` tests, then you
    can setup your database tables once before your test suite runs. Any
    changes made to your tables by the tests will be rolled back automatically.

    Here's an example::

        from piccolo.testing.test_case import AsyncTransactionTest


        class TestBandEndpoint(AsyncTransactionTest):

            async def test_band_response(self):
                \"\"\"
                Make sure the endpoint returns a 200.
                \"\"\"
                band = Band({Band.name: "Pythonistas"})
                await band.save()

                # Using an API testing client, like httpx:
                response = await client.get(f"/bands/{band.id}/")
                self.assertEqual(response.status_code, 200)

    We add a ``Band`` to the database, but any subsequent tests won't see it,
    as the changes are rolled back automatically.

    """

    # We use `engine_finder` to find the current `Engine`, but you can
    # explicity set it here if you prefer:
    #
    # class MyTest(AsyncTransactionTest):
    #     db = DB
    #
    #     ...
    #
    db: t.Optional[Engine] = None

    async def asyncSetUp(self) -> None:
        db = self.db or engine_finder()
        assert db is not None
        self.transaction = db.transaction()
        # This is only available in Python 3.11 and above:
        await self.enterAsyncContext(cm=self.transaction)  # type: ignore

    async def asyncTearDown(self):
        await super().asyncTearDown()
        await self.transaction.rollback()
