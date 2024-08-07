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
    Used for tests where we need to create Piccolo tables - they will
    automatically be created and dropped.

    For example::

        class TestBand(TableTest):
            tables = [Band]

            def test_example(self):
                ...

    """

    tables: t.List[t.Type[Table]]

    def setUp(self) -> None:
        create_db_tables_sync(*self.tables)

    def tearDown(self) -> None:
        drop_db_tables_sync(*self.tables)


class AsyncTableTest(IsolatedAsyncioTestCase):

    tables: t.List[t.Type[Table]]

    async def asyncSetUp(self) -> None:
        await create_db_tables(*self.tables)

    async def asyncTearDown(self) -> None:
        await drop_db_tables(*self.tables)


class AsyncTransactionTest(IsolatedAsyncioTestCase):
    """
    Wraps each test in a transaction, which is automatically rolled back at the
    end.

    .. warning::
        Python 3.11 and above only.

    """

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
