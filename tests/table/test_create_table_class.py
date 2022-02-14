from unittest import TestCase

from piccolo.columns import Varchar
from piccolo.table import create_table_class


class TestCreateTableClass(TestCase):
    def test_create_table_class(self):
        """
        Make sure a basic `Table` can be created successfully.
        """
        _Table = create_table_class(class_name="MyTable")
        self.assertEqual(_Table._meta.tablename, "my_table")

        _Table = create_table_class(
            class_name="MyTable", class_kwargs={"tablename": "my_table_1"}
        )
        self.assertEqual(_Table._meta.tablename, "my_table_1")

        column = Varchar()
        _Table = create_table_class(
            class_name="MyTable", class_members={"name": column}
        )
        self.assertIn(column, _Table._meta.columns)

    def test_protected_tablenames(self):
        """
        Make sure that the logic around protected tablenames still works as
        expected.
        """
        with self.assertRaises(ValueError):
            create_table_class(class_name="User")

        with self.assertRaises(ValueError):
            create_table_class(
                class_name="MyUser", class_kwargs={"tablename": "user"}
            )

        # This shouldn't raise an error:
        create_table_class(
            class_name="User", class_kwargs={"tablename": "my_user"}
        )
