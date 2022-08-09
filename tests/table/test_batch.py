import asyncio
import math

from tests.base import DBTestCase, postgres_only
from tests.example_apps.music.tables import Manager


@postgres_only
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

    async def run_batch_extra_node(self, batch_size, node):
        row_count = 0
        iterations = 0

        async with await Manager.select().batch(
            batch_size=batch_size, node=node
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

    def test_batch_extra_node(self):
        from ..postgres_conf import DB

        row_count = 1000
        self.insert_many_rows(row_count)

        # passing the test database as a read_replica to
        # test if the batch method node argument works
        DB.extra_nodes["read_replica"] = DB

        batch_size = 10
        node = "read_replica"

        _row_count, iterations = asyncio.run(
            self.run_batch_extra_node(batch_size=batch_size, node=node),
            debug=True,
        )

        _iterations = math.ceil(row_count / batch_size)

        self.assertEqual(_row_count, row_count)
        self.assertEqual(iterations, _iterations)


@postgres_only
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
