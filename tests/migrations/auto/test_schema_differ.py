import typing as t
from unittest import TestCase

from piccolo.columns.column_types import Varchar
from piccolo.migrations.auto import (
    DiffableTable,
    SchemaDiffer,
)


class TestSchemaDiffer(TestCase):
    def test_rename_table(self):
        """
        Test renaming a table.
        """
        name_column = Varchar()
        name_column._meta.name = "name"

        schema: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Act", tablename="act", columns=[name_column]
            )
        ]
        schema_snapshot: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Band", tablename="band", columns=[name_column]
            )
        ]

        schema_differ = SchemaDiffer(
            schema=schema, schema_snapshot=schema_snapshot, auto_input="y"
        )

        self.assertTrue(len(schema_differ.rename_tables) == 1)
        self.assertEqual(
            schema_differ.rename_tables[0],
            "manager.rename_table(old_class_name='Band', new_class_name='Act', new_tablename='act')",  # noqa
        )

        self.assertEqual(schema_differ.create_tables, [])
        self.assertEqual(schema_differ.drop_tables, [])

    def test_add_column(self):
        """
        Test adding a column to an existing table.
        """
        pass
