from unittest import TestCase

from piccolo.table import Table


class TestMeta(TestCase):
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
