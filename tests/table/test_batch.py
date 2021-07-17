import asyncio
import math

from ..base import DBTestCase
from ..example_app.tables import Manager


class TestBatchSelect(DBTestCase):
    def _check_results(self, batch):
        """
        Make sure the data is returned in the correct format.
        """
        self.assertTrue(type(batch) == list)
        if len(batch) > 0:
            row = batch[0]
            self.assertTrue(type(row) == dict)
            self.assertTrue("name" in row.keys())
            self.assertTrue("id" in row.keys())

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

        self.assertTrue(_row_count == row_count)
        self.assertTrue(iterations == _iterations)


class TestBatchObjects(DBTestCase):
    def _check_results(self, batch):
        """
        Make sure the data is returned in the correct format.
        """
        self.assertTrue(type(batch) == list)
        if len(batch) > 0:
            row = batch[0]
            self.assertTrue(isinstance(row, Manager))

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

        self.assertTrue(_row_count == row_count)
        self.assertTrue(iterations == _iterations)
