from unittest import TestCase
from unittest.mock import MagicMock, patch

from piccolo.columns import Secret
from piccolo.columns.column_types import (
    JSON,
    JSONB,
    Array,
    Email,
    ForeignKey,
    Varchar,
)
from piccolo.table import TABLENAME_WARNING, Table
from tests.example_apps.music.tables import Band


class TestMetaClass(TestCase):
    def test_tablename(self):
        self.assertEqual(Band._meta.tablename, "band")

    def test_protected_table_names(self):
        """
        Some tablenames are forbidden because they're reserved words in the
        database, and can potentially cause issues.
        """
        expected_warning = TABLENAME_WARNING.format(tablename="user")

        with patch("piccolo.table.warnings") as warnings:

            class User(Table):
                pass

            warnings.warn.assert_called_with(expected_warning)

        with patch("piccolo.table.warnings") as warnings:

            class MyUser(Table, tablename="user"):
                pass

            warnings.warn.assert_called_with(expected_warning)

    def test_help_text(self):
        """
        Make sure help_text can be set for the Table.
        """
        help_text = "The manager of a band."

        class Manager(Table, help_text=help_text):
            pass

        self.assertEqual(Manager._meta.help_text, help_text)

    def test_schema(self):
        """
        Make sure schema can be set for the Table.
        """
        schema = "schema_1"

        class Manager(Table, schema=schema):
            pass

        self.assertEqual(Manager._meta.schema, schema)

    @patch("piccolo.table.warnings")
    def test_schema_from_tablename(self, warnings: MagicMock):
        """
        If the tablename contains a '.' we extract the schema name.
        """
        table = "manager"
        schema = "schema_1"

        tablename = f"{schema}.{table}"

        class Manager(Table, tablename=tablename):
            pass

        self.assertEqual(Manager._meta.schema, schema)
        self.assertEqual(Manager._meta.tablename, table)

        warnings.warn.assert_called_once_with(
            "There's a '.' in the tablename - please use the `schema` "
            "argument instead."
        )

    def test_foreign_key_columns(self):
        """
        Make sure TableMeta.foreign_keys and TableMeta.foreign_key_references
        are setup correctly.
        """

        class TableA(Table):
            pass

        class TableB(Table):
            table_a = ForeignKey(references=TableA)

        self.assertEqual(TableB._meta.foreign_key_columns, [TableB.table_a])
        self.assertEqual(TableA._meta.foreign_key_references, [TableB.table_a])

    def test_secret_columns(self):
        """
        Make sure TableMeta.secret_columns are setup correctly.
        """

        class Classified(Table):
            top_secret = Secret()

        self.assertEqual(
            Classified._meta.secret_columns, [Classified.top_secret]
        )

    def test_json_columns(self):
        """
        Make sure TableMeta.json_columns are setup correctly.
        """

        class MyTable(Table):
            column_a = JSON()
            column_b = JSONB()

        self.assertEqual(
            MyTable._meta.json_columns, [MyTable.column_a, MyTable.column_b]
        )

    def test_email_columns(self):
        """
        Make sure ``TableMeta.email_columns`` are setup correctly.
        """

        class MyTable(Table):
            column_a = Email()
            column_b = Varchar()

        self.assertEqual(MyTable._meta.email_columns, [MyTable.column_a])

    def test_arry_columns(self):
        """
        Make sure ``TableMeta.array_columns`` are setup correctly.
        """

        class MyTable(Table):
            column_a = Array(Varchar())
            column_b = Varchar()

        self.assertEqual(MyTable._meta.array_columns, [MyTable.column_a])

    def test_id_column(self):
        """
        Makes sure an id column is added.
        """

        class TableA(Table):
            pass

        self.assertTrue(hasattr(TableA, "id"))
