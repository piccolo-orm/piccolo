from __future__ import annotations

import ast
import typing as t
from unittest import TestCase
from unittest.mock import MagicMock, patch

from piccolo.apps.schema.commands.generate import (
    OutputSchema,
    generate,
    get_output_schema,
)
from piccolo.columns.column_types import Varchar
from piccolo.table import Table
from piccolo.utils.sync import run_sync
from tests.base import postgres_only
from tests.mega_table import MegaTable, SmallTable


@postgres_only
class TestGenerate(TestCase):
    def setUp(self):
        for table_class in (SmallTable, MegaTable):
            table_class.create_table().run_sync()

    def tearDown(self):
        for table_class in (MegaTable, SmallTable):
            table_class.alter().drop_table().run_sync()

    def _compare_table_columns(
        self, table_1: t.Type[Table], table_2: t.Type[Table]
    ):
        """
        Make sure that for each column in table_1, there is a corresponding
        column in table_2 of the same type.
        """
        column_names = [
            column._meta.name for column in table_1._meta.non_default_columns
        ]
        for column_name in column_names:
            col_1 = table_1._meta.get_column_by_name(column_name)
            col_2 = table_2._meta.get_column_by_name(column_name)

            # Make sure they're the same type
            self.assertEqual(type(col_1), type(col_2))

            # Make sure they're both nullable or not
            self.assertEqual(col_1._meta.null, col_2._meta.null)

            # Make sure the max length is the same
            if isinstance(col_1, Varchar) and isinstance(col_2, Varchar):
                self.assertEqual(col_1.length, col_2.length)

            # Make sure the unique constraint is the same
            self.assertEqual(col_1._meta.unique, col_2._meta.unique)

    def test_get_output_schema(self):
        """
        Make sure that the a Piccolo schema can be generated from the database.
        """
        output_schema: OutputSchema = run_sync(get_output_schema())

        self.assertTrue(len(output_schema.warnings) == 0)
        self.assertTrue(len(output_schema.tables) == 2)
        self.assertTrue(len(output_schema.imports) > 0)

        MegaTable_ = output_schema.get_table_with_name("MegaTable")
        self._compare_table_columns(MegaTable, MegaTable_)

        SmallTable_ = output_schema.get_table_with_name("SmallTable")
        self._compare_table_columns(SmallTable, SmallTable_)

    @patch("piccolo.apps.schema.commands.generate.print")
    def test_generate(self, print_: MagicMock):
        """
        Test the main generate command runs without errors.
        """
        run_sync(generate())
        file_contents = print_.call_args[0][0]

        # Make sure the output is valid Python code (will raise a SyntaxError
        # exception otherwise).
        ast.parse(file_contents)
