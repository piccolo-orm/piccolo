from piccolo.columns.column_types import Integer
from piccolo.table import Table
from piccolo.testing.test_case import AsyncTableTest
from tests.base import sqlite_only


class MyTable(Table):
    integer = Integer()


@sqlite_only
class TestInteger(AsyncTableTest):
    tables = [MyTable]

    async def test_large_integer(self):
        """
        Make sure large integers can be inserted and retrieved correctly.

        There was a bug with this in SQLite:

        https://github.com/piccolo-orm/piccolo/issues/1127

        """
        integer = 625757527765811240

        row = MyTable(integer=integer)
        await row.save()

        _row = MyTable.objects().first().run_sync()
        assert _row is not None

        self.assertEqual(_row.integer, integer)
