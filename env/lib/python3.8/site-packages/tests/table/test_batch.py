import asyncio
import math
from unittest import TestCase

from piccolo.columns import Varchar
from piccolo.engine.finder import engine_finder
from piccolo.engine.postgres import AsyncBatch, PostgresEngine
from piccolo.table import Table
from piccolo.utils.sync import run_sync
from tests.base import AsyncMock, DBTestCase, engines_only
from tests.example_apps.music.tables import Manager


class TestBatchSelect(DBTestCase):
    def _check_results(self, batch):
        """
        Make sure the data is returned in the correct format.
        """
        self.assertEqual(type(batch), list)
        if len(batch) > 0:
            row = batch[0]
            self.assertEqual(type(row), dict)
            self.assertIn("name", row.keys())
            self.assertIn("id", row.keys())

    async def run_batch(self, batch_size):
        row_count = 0
        iterations = 0

        async with await Manager.select().batch(
            batch_size=batch_size
        ) as batch:
            async for _batch in batch:
                self._check_results(_batch)
                _row_count = len(_batch)
                row_count += _row_count
                iterations += 1

        return row_count, iterations

    def test_batch(self):
        row_count = 1000
        self.insert_many_rows(row_count)

        batch_size = 10

        _row_count, iterations = asyncio.run(
            self.run_batch(batch_size=batch_size), debug=True
        )

        _iterations = math.ceil(row_count / batch_size)

        self.assertEqual(_row_count, row_count)
        self.assertEqual(iterations, _iterations)


class TestBatchObjects(DBTestCase):
    def _check_results(self, batch):
        """
        Make sure the data is returned in the correct format.
        """
        self.assertEqual(type(batch), list)
        if len(batch) > 0:
            row = batch[0]
            self.assertIsInstance(row, Manager)

    async def run_batch(self, batch_size):
        row_count = 0
        iterations = 0

        async with await Manager.objects().batch(
            batch_size=batch_size
        ) as batch:
            async for _batch in batch:
                self._check_results(_batch)
                _row_count = len(_batch)
                row_count += _row_count
                iterations += 1

        return row_count, iterations

    def test_batch(self):
        row_count = 1000
        self.insert_many_rows(row_count)

        batch_size = 10

        _row_count, iterations = asyncio.run(
            self.run_batch(batch_size=batch_size), debug=True
        )

        _iterations = math.ceil(row_count / batch_size)

        self.assertEqual(_row_count, row_count)
        self.assertEqual(iterations, _iterations)


@engines_only("postgres", "cockroach")
class TestBatchNodeArg(TestCase):
    def test_batch_extra_node(self):
        """
        Make sure the batch methods can accept a node argument.
        """

        # Get the test database credentials:
        test_engine = engine_finder()

        EXTRA_NODE = AsyncMock(spec=PostgresEngine(config=test_engine.config))

        DB = PostgresEngine(
            config=test_engine.config,
            extra_nodes={"read_1": EXTRA_NODE},
        )

        class Manager(Table, db=DB):
            name = Varchar()

        # Testing `select`
        response = run_sync(Manager.select().batch(node="read_1"))
        self.assertIsInstance(response, AsyncBatch)
        self.assertTrue(EXTRA_NODE.get_new_connection.called)
        EXTRA_NODE.reset_mock()

        # Testing `objects`
        response = run_sync(Manager.objects().batch(node="read_1"))
        self.assertIsInstance(response, AsyncBatch)
        self.assertTrue(EXTRA_NODE.get_new_connection.called)
