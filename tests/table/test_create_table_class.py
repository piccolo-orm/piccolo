from unittest import TestCase
from unittest.mock import patch

from piccolo.columns import Varchar
from piccolo.table import TABLENAME_WARNING, create_table_class


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
        expected_warning = TABLENAME_WARNING.format(tablename="user")

        with patch("piccolo.table.warnings") as warnings:
            create_table_class(class_name="User")
            warnings.warn.assert_called_once_with(expected_warning)

        with patch("piccolo.table.warnings") as warnings:
            create_table_class(
                class_name="MyUser", class_kwargs={"tablename": "user"}
            )
            warnings.warn.assert_called_once_with(expected_warning)

        # This shouldn't output a warning:
        with patch("piccolo.table.warnings") as warnings:
            create_table_class(
                class_name="User", class_kwargs={"tablename": "my_user"}
            )
            warnings.warn.assert_not_called()
