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
