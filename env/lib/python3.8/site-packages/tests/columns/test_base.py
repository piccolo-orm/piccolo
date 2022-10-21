from enum import Enum
from unittest import TestCase

from piccolo.columns.choices import Choice
from piccolo.columns.column_types import Integer, Varchar
from piccolo.table import Table
from tests.example_apps.music.tables import Band, Manager


class MyTable(Table):
    name = Varchar()


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
        self.assertEqual(column._meta.help_text, help_text)


class TestSecretParameter(TestCase):
    def test_secret_parameter(self):
        """
        Test adding secret parameter to a column.
        """
        secret = False
        column = Varchar(secret=secret)
        self.assertEqual(column._meta.secret, secret)


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


class TestEquals(TestCase):
    def test_non_column(self):
        """
        Make sure non-column values don't match.
        """
        for value in (1, "abc", None):
            self.assertFalse(Manager.name._equals(value))

    def test_equals(self):
        """
        Test basic usage.
        """
        self.assertTrue(Manager.name._equals(Manager.name))

    def test_same_name(self):
        """
        Make sure that columns with the same name, but on different tables,
        don't match.
        """
        self.assertFalse(Manager.name._equals(Band.name))

    def test_including_joins(self):
        """
        Make sure `including_joins` arg works correctly.
        """
        self.assertTrue(Band.manager.name._equals(Manager.name))

        self.assertFalse(
            Band.manager.name._equals(Manager.name, including_joins=True)
        )
