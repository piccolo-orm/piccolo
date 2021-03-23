from unittest import TestCase

from piccolo.table import Table

from ..example_app.tables import Band


class TestMetaClass(TestCase):
    def test_tablename(self):
        self.assertEqual(Band._meta.tablename, "band")

    def test_protected_table_names(self):
        """
        Some tablenames are forbidden because they're reserved words in the
        database, and can potentially cause issues.
        """
        with self.assertRaises(ValueError):

            class User(Table):
                pass

        with self.assertRaises(ValueError):

            class MyUser(Table, tablename="user"):
                pass

    def test_help_text(self):
        """
        Make sure help_text can be set for the Table.
        """
        help_text = "The manager of a band."

        class Manager(Table, help_text=help_text):
            pass

        self.assertEqual(Manager._meta.help_text, help_text)
