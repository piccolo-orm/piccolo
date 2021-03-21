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


class TestCopy(TestCase):
    def test_copy(self):
        """
        Try copying columns.
        """
        column = MyTable.name
        new_column = column.copy()
        self.assertNotEqual(id(column), id(new_column))
        self.assertNotEqual(id(column._meta), id(new_column._meta))
        self.assertNotEqual(
            id(column._meta.call_chain), id(new_column._meta.call_chain)
        )


class TestHelpText(TestCase):
    def test_help_text(self):
        """
        Test adding help text to a column.
        """
        help_text = "This is some important help text for users."
        column = Varchar(help_text=help_text)
        self.assertTrue(column._meta.help_text == help_text)
