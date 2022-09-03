from __future__ import annotations

import typing as t
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from piccolo.apps.migrations.auto import DiffableTable, SchemaDiffer
from piccolo.columns.column_types import Numeric, Varchar


class TestSchemaDiffer(TestCase):

    maxDiff = None

    def test_add_table(self):
        """
        Test adding a new table.
        """
        name_column = Varchar()
        name_column._meta.name = "name"
        schema: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Band", tablename="band", columns=[name_column]
            )
        ]
        schema_snapshot: t.List[DiffableTable] = []
        schema_differ = SchemaDiffer(
            schema=schema, schema_snapshot=schema_snapshot, auto_input="y"
        )

        create_tables = schema_differ.create_tables
        self.assertTrue(len(create_tables.statements) == 1)
        self.assertEqual(
            create_tables.statements[0],
            "manager.add_table('Band', tablename='band')",
        )

        new_table_columns = schema_differ.new_table_columns
        self.assertTrue(len(new_table_columns.statements) == 1)
        self.assertEqual(
            new_table_columns.statements[0],
            "manager.add_column(table_class_name='Band', tablename='band', column_name='name', db_column_name='name', column_class_name='Varchar', column_class=Varchar, params={'length': 255, 'default': '', 'null': False, 'primary_key': False, 'unique': False, 'index': False, 'index_method': IndexMethod.btree, 'choices': None, 'db_column_name': None, 'secret': False})",  # noqa
        )

    def test_drop_table(self):
        """
        Test dropping an existing table.
        """
        schema: t.List[DiffableTable] = []
        schema_snapshot: t.List[DiffableTable] = [
            DiffableTable(class_name="Band", tablename="band", columns=[])
        ]
        schema_differ = SchemaDiffer(
            schema=schema, schema_snapshot=schema_snapshot, auto_input="y"
        )

        self.assertTrue(len(schema_differ.drop_tables.statements) == 1)
        self.assertEqual(
            schema_differ.drop_tables.statements[0],
            "manager.drop_table(class_name='Band', tablename='band')",
        )

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

        self.assertTrue(len(schema_differ.rename_tables.statements) == 1)
        self.assertEqual(
            schema_differ.rename_tables.statements[0],
            "manager.rename_table(old_class_name='Band', old_tablename='band', new_class_name='Act', new_tablename='act')",  # noqa
        )

        self.assertEqual(schema_differ.create_tables.statements, [])
        self.assertEqual(schema_differ.drop_tables.statements, [])

    def test_add_column(self):
        """
        Test adding a column to an existing table.
        """
        name_column = Varchar()
        name_column._meta.name = "name"

        genre_column = Varchar()
        genre_column._meta.name = "genre"

        schema: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Band",
                tablename="band",
                columns=[name_column, genre_column],
            )
        ]
        schema_snapshot: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Band",
                tablename="band",
                columns=[name_column],
            )
        ]

        schema_differ = SchemaDiffer(
            schema=schema, schema_snapshot=schema_snapshot, auto_input="y"
        )

        self.assertTrue(len(schema_differ.add_columns.statements) == 1)
        self.assertEqual(
            schema_differ.add_columns.statements[0],
            "manager.add_column(table_class_name='Band', tablename='band', column_name='genre', db_column_name='genre', column_class_name='Varchar', column_class=Varchar, params={'length': 255, 'default': '', 'null': False, 'primary_key': False, 'unique': False, 'index': False, 'index_method': IndexMethod.btree, 'choices': None, 'db_column_name': None, 'secret': False})",  # noqa
        )

    def test_drop_column(self):
        """
        Test dropping a column from an existing table.
        """
        name_column = Varchar()
        name_column._meta.name = "name"

        genre_column = Varchar()
        genre_column._meta.name = "genre"

        schema: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Band",
                tablename="band",
                columns=[name_column],
            )
        ]
        schema_snapshot: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Band",
                tablename="band",
                columns=[name_column, genre_column],
            )
        ]

        schema_differ = SchemaDiffer(
            schema=schema, schema_snapshot=schema_snapshot, auto_input="y"
        )

        self.assertTrue(len(schema_differ.drop_columns.statements) == 1)
        self.assertEqual(
            schema_differ.drop_columns.statements[0],
            "manager.drop_column(table_class_name='Band', tablename='band', column_name='genre', db_column_name='genre')",  # noqa
        )

    def test_rename_column(self):
        """
        Test renaming a column in an existing table.
        """
        # We're going to rename the 'name' column to 'title'
        name_column = Varchar()
        name_column._meta.name = "name"

        title_column = Varchar()
        title_column._meta.name = "title"

        schema_snapshot: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Band",
                tablename="band",
                columns=[title_column],
            )
        ]
        schema: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Band",
                tablename="band",
                columns=[name_column],
            )
        ]

        # Test 1 - Tell Piccolo the column was renamed
        schema_differ = SchemaDiffer(
            schema=schema, schema_snapshot=schema_snapshot, auto_input="y"
        )
        self.assertEqual(schema_differ.add_columns.statements, [])
        self.assertEqual(schema_differ.drop_columns.statements, [])
        self.assertEqual(
            schema_differ.rename_columns.statements,
            [
                "manager.rename_column(table_class_name='Band', tablename='band', old_column_name='title', new_column_name='name', old_db_column_name='title', new_db_column_name='name')"  # noqa
            ],
        )

        # Test 2 - Tell Piccolo the column wasn't renamed
        schema_differ = SchemaDiffer(
            schema=schema, schema_snapshot=schema_snapshot, auto_input="n"
        )
        self.assertEqual(
            schema_differ.add_columns.statements,
            [
                "manager.add_column(table_class_name='Band', tablename='band', column_name='name', db_column_name='name', column_class_name='Varchar', column_class=Varchar, params={'length': 255, 'default': '', 'null': False, 'primary_key': False, 'unique': False, 'index': False, 'index_method': IndexMethod.btree, 'choices': None, 'db_column_name': None, 'secret': False})"  # noqa: E501
            ],
        )
        self.assertEqual(
            schema_differ.drop_columns.statements,
            [
                "manager.drop_column(table_class_name='Band', tablename='band', column_name='title', db_column_name='title')"  # noqa: E501
            ],
        )
        self.assertTrue(schema_differ.rename_columns.statements == [])

    @patch("piccolo.apps.migrations.auto.schema_differ.input")
    def test_rename_multiple_columns(self, input: MagicMock):
        """
        Make sure renaming columns works when several columns have been
        renamed.
        """
        # We're going to rename a1 to a2, and b1 to b2.
        a1 = Varchar()
        a1._meta.name = "a1"

        a2 = Varchar()
        a2._meta.name = "a2"

        b1 = Varchar()
        b1._meta.name = "b1"

        b2 = Varchar()
        b2._meta.name = "b2"

        schema_snapshot: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Band",
                tablename="band",
                columns=[a1, b1],
            )
        ]
        schema: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Band",
                tablename="band",
                columns=[a2, b2],
            )
        ]

        def mock_input(value: str):
            """
            We need to dynamically set the return value based on what's passed
            in.
            """
            return (
                "y"
                if value
                in (
                    "Did you rename the `a1` column to `a2` on the `Band` table? (y/N)",  # noqa: E501
                    "Did you rename the `b1` column to `b2` on the `Band` table? (y/N)",  # noqa: E501
                )
                else "n"
            )

        input.side_effect = mock_input

        schema_differ = SchemaDiffer(
            schema=schema, schema_snapshot=schema_snapshot
        )
        self.assertEqual(schema_differ.add_columns.statements, [])
        self.assertEqual(schema_differ.drop_columns.statements, [])
        self.assertEqual(
            schema_differ.rename_columns.statements,
            [
                "manager.rename_column(table_class_name='Band', tablename='band', old_column_name='a1', new_column_name='a2', old_db_column_name='a1', new_db_column_name='a2')",  # noqa: E501
                "manager.rename_column(table_class_name='Band', tablename='band', old_column_name='b1', new_column_name='b2', old_db_column_name='b1', new_db_column_name='b2')",  # noqa: E501
            ],
        )

        self.assertEqual(
            input.call_args_list,
            [
                call(
                    "Did you rename the `a1` column to `a2` on the `Band` table? (y/N)"  # noqa: E501
                ),
                call(
                    "Did you rename the `b1` column to `b2` on the `Band` table? (y/N)"  # noqa: E501
                ),
            ],
        )

    @patch("piccolo.apps.migrations.auto.schema_differ.input")
    def test_rename_some_columns(self, input: MagicMock):
        """
        Make sure that some columns can be marked as renamed, and others are
        dropped / created.
        """
        # We're going to rename a1 to a2, but want b1 to be dropped, and b2 to
        # be created.
        a1 = Varchar()
        a1._meta.name = "a1"

        a2 = Varchar()
        a2._meta.name = "a2"

        b1 = Varchar()
        b1._meta.name = "b1"

        b2 = Varchar()
        b2._meta.name = "b2"

        schema_snapshot: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Band",
                tablename="band",
                columns=[a1, b1],
            )
        ]
        schema: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Band",
                tablename="band",
                columns=[a2, b2],
            )
        ]

        def mock_input(value: str):
            """
            We need to dynamically set the return value based on what's passed
            in.
            """
            return (
                "y"
                if value
                == "Did you rename the `a1` column to `a2` on the `Band` table? (y/N)"  # noqa: E501
                else "n"
            )

        input.side_effect = mock_input

        schema_differ = SchemaDiffer(
            schema=schema, schema_snapshot=schema_snapshot
        )
        self.assertEqual(
            schema_differ.add_columns.statements,
            [
                "manager.add_column(table_class_name='Band', tablename='band', column_name='b2', db_column_name='b2', column_class_name='Varchar', column_class=Varchar, params={'length': 255, 'default': '', 'null': False, 'primary_key': False, 'unique': False, 'index': False, 'index_method': IndexMethod.btree, 'choices': None, 'db_column_name': None, 'secret': False})"  # noqa: E501
            ],
        )
        self.assertEqual(
            schema_differ.drop_columns.statements,
            [
                "manager.drop_column(table_class_name='Band', tablename='band', column_name='b1', db_column_name='b1')"  # noqa: E501
            ],
        )
        self.assertEqual(
            schema_differ.rename_columns.statements,
            [
                "manager.rename_column(table_class_name='Band', tablename='band', old_column_name='a1', new_column_name='a2', old_db_column_name='a1', new_db_column_name='a2')",  # noqa: E501
            ],
        )

        self.assertEqual(
            input.call_args_list,
            [
                call(
                    "Did you rename the `a1` column to `a2` on the `Band` table? (y/N)"  # noqa: E501
                ),
                call(
                    "Did you rename the `b1` column to `b2` on the `Band` table? (y/N)"  # noqa: E501
                ),
            ],
        )

    def test_alter_column_precision(self):
        price_1 = Numeric(digits=(4, 2))
        price_1._meta.name = "price"

        price_2 = Numeric(digits=(5, 2))
        price_2._meta.name = "price"

        schema: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Ticket",
                tablename="ticket",
                columns=[price_1],
            )
        ]
        schema_snapshot: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Ticket",
                tablename="ticket",
                columns=[price_2],
            )
        ]

        schema_differ = SchemaDiffer(
            schema=schema, schema_snapshot=schema_snapshot, auto_input="y"
        )

        self.assertTrue(len(schema_differ.alter_columns.statements) == 1)
        self.assertEqual(
            schema_differ.alter_columns.statements[0],
            "manager.alter_column(table_class_name='Ticket', tablename='ticket', column_name='price', db_column_name='price', params={'digits': (4, 2)}, old_params={'digits': (5, 2)}, column_class=Numeric, old_column_class=Numeric)",  # noqa
        )

    def test_db_column_name(self):
        """
        Make sure alter statements use the ``db_column_name`` if provided.

        https://github.com/piccolo-orm/piccolo/issues/513

        """
        price_1 = Numeric(digits=(4, 2), db_column_name="custom")
        price_1._meta.name = "price"

        price_2 = Numeric(digits=(5, 2), db_column_name="custom")
        price_2._meta.name = "price"

        schema: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Ticket",
                tablename="ticket",
                columns=[price_1],
            )
        ]
        schema_snapshot: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Ticket",
                tablename="ticket",
                columns=[price_2],
            )
        ]

        schema_differ = SchemaDiffer(
            schema=schema, schema_snapshot=schema_snapshot, auto_input="y"
        )

        self.assertTrue(len(schema_differ.alter_columns.statements) == 1)
        self.assertEqual(
            schema_differ.alter_columns.statements[0],
            "manager.alter_column(table_class_name='Ticket', tablename='ticket', column_name='price', db_column_name='custom', params={'digits': (4, 2)}, old_params={'digits': (5, 2)}, column_class=Numeric, old_column_class=Numeric)",  # noqa
        )

    def test_alter_default(self):
        pass
