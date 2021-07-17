from unittest import TestCase

from piccolo.columns.column_types import Varchar
from piccolo.table import Table

from ..base import postgres_only


class MyTable(Table):
    name = Varchar(length=10)


@postgres_only
class TestVarchar(TestCase):
    """
    SQLite doesn't enforce any constraints on max character length.

    https://www.sqlite.org/faq.html#q9

    Might consider enforncing this at the ORM level instead in the future.
    """

    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_length(self):
        row = MyTable(name="bob")
        row.save().run_sync()

        with self.assertRaises(Exception):
            row.name = "bob123456789"
            row.save().run_sync()
