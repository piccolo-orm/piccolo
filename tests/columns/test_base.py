from enum import Enum
from unittest import TestCase

from piccolo.columns.choices import Choice
from piccolo.columns.column_types import Integer, Varchar
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


class TestChoices(TestCase):
    def test_choices(self):
        """
        Test adding choices to a column.
        """

        class Title(Enum):
            mr = 1
            mrs = 2

        column = Integer(choices=Title)
        self.assertEqual(column._meta.choices, Title)

    def test_invalid_types(self):
        """
        Test adding choices to a column, which are the wrong type.
        """

        class Title(Enum):
            mr = 1
            mrs = 2

        with self.assertRaises(ValueError):
            Varchar(choices=Title)

    def test_get_choices_dict(self):
        """
        Test ``get_choices_dict``.
        """

        class Title(Enum):
            mr = 1
            mrs = 2

        column = Integer(choices=Title)

        self.assertEqual(
            column._meta.get_choices_dict(),
            {
                "mr": {"display_name": "Mr", "value": 1},
                "mrs": {"display_name": "Mrs", "value": 2},
            },
        )

    def test_get_choices_dict_without_choices(self):
        """
        Test ``get_choices_dict``, with no choices set.
        """
        column = Integer()
        self.assertEqual(column._meta.get_choices_dict(), None)

    def test_get_choices_dict_with_custom_names(self):
        """
        Test ``get_choices_dict``, when ``Choice`` is used.
        """

        class Title(Enum):
            mr = Choice(value=1, display_name="Mr.")
            mrs = Choice(value=2, display_name="Mrs.")

        column = Integer(choices=Title)
        self.assertEqual(
            column._meta.get_choices_dict(),
            {
                "mr": {"display_name": "Mr.", "value": 1},
                "mrs": {"display_name": "Mrs.", "value": 2},
            },
        )
