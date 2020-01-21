from unittest import TestCase

from piccolo.columns.column_types import Varchar
from piccolo.table import Table


class MyTable(Table):
    name = Varchar()


class TestColumn(TestCase):
    def test_like_raises(self):
        """
        Make sure an invalid 'like' argument raises an exception. Should
        contain a % symbol.
        """
        column = MyTable.name
        with self.assertRaises(ValueError):
            column.like("guido")

        with self.assertRaises(ValueError):
            column.ilike("guido")

        # Make sure valid args don't raise an exception.
        for arg in ["%guido", "guido%", "%guido%"]:
            column.like("%foo")
            column.ilike("foo%")
