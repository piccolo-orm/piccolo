from piccolo.columns.column_types import Varchar
from piccolo.table import Table
from piccolo.testing.test_case import TableTest
from tests.base import engines_only


class MyTable(Table):
    name = Varchar(length=10)


@engines_only("postgres", "cockroach")
class TestVarchar(TableTest):
    """
    SQLite doesn't enforce any constraints on max character length.

    https://www.sqlite.org/faq.html#q9

    Might consider enforcing this at the ORM level instead in the future.
    """

    tables = [MyTable]

    def test_length(self):
        row = MyTable(name="bob")
        row.save().run_sync()

        with self.assertRaises(Exception):
            row.name = "bob123456789"
            row.save().run_sync()
