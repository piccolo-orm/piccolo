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
from piccolo.columns.base import Column
from piccolo.columns.column_types import (
    ForeignKey,
    Integer,
    Timestamp,
    Varchar,
)
from piccolo.columns.indexes import IndexMethod
from piccolo.engine import Engine, engine_finder
from piccolo.table import Table
from piccolo.utils.sync import run_sync
from tests.base import postgres_only
from tests.example_apps.mega.tables import MegaTable, SmallTable


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
    def test_generate_command(self, print_: MagicMock):
        """
        Test the main generate command runs without errors.
        """
        run_sync(generate())
        file_contents = print_.call_args[0][0]

        # Make sure the output is valid Python code (will raise a SyntaxError
        # exception otherwise).
        ast.parse(file_contents)

    def test_unknown_column_type(self):
        """
        Make sure unknown column types are handled gracefully.
        """

        class Box(Column):
            """
            A column type which isn't supported by Piccolo officially yet.
            """

            pass

        MegaTable.alter().add_column("my_column", Box()).run_sync()

        output_schema: OutputSchema = run_sync(get_output_schema())

        # Make sure there's a warning.
        self.assertEqual(
            output_schema.warnings, ["mega_table.my_column ['box']"]
        )

        # Make sure the column type of the generated table is just ``Column``.
        for table in output_schema.tables:
            if table.__name__ == "MegaTable":
                self.assertEqual(
                    output_schema.tables[1].my_column.__class__.__name__,
                    "Column",
                )

    def test_generate_required_tables(self):
        """
        Make sure only tables passed to `tablenames` are created.
        """
        output_schema: OutputSchema = run_sync(
            get_output_schema(include=[SmallTable._meta.tablename])
        )
        self.assertEqual(len(output_schema.tables), 1)
        SmallTable_ = output_schema.get_table_with_name("SmallTable")
        self._compare_table_columns(SmallTable, SmallTable_)

    def test_exclude_table(self):
        """
        Make sure exclude works.
        """
        output_schema: OutputSchema = run_sync(
            get_output_schema(exclude=[MegaTable._meta.tablename])
        )
        self.assertEqual(len(output_schema.tables), 1)
        SmallTable_ = output_schema.get_table_with_name("SmallTable")
        self._compare_table_columns(SmallTable, SmallTable_)

    def test_self_referencing_fk(self):
        """
        Make sure self-referencing foreign keys are handled correctly.
        """

        MegaTable.alter().add_column("self_referencing_fk", ForeignKey("self")).run_sync()

        output_schema: OutputSchema = run_sync(get_output_schema())

        # Make sure the 'references' value of the generated column is "self".
        for table in output_schema.tables:
            if table.__name__ == "MegaTable":
                self.assertEqual(
                    output_schema.tables[1].self_referencing_fk,
                    "self"
                )

###############################################################################


class Concert(Table):
    name = Varchar(index=True, index_method=IndexMethod.hash)
    time = Timestamp(
        index=True
    )  # Testing a column with the same name as a Postgres data type.
    capacity = Integer(index=False)


@postgres_only
class TestGenerateWithIndexes(TestCase):
    def setUp(self):
        Concert.create_table().run_sync()

    def tearDown(self):
        Concert.alter().drop_table(if_exists=True).run_sync()

    def test_index(self):
        """
        Make sure that a table with an index is reflected correctly.
        """
        output_schema: OutputSchema = run_sync(get_output_schema())
        Concert_ = output_schema.tables[0]

        self.assertEqual(Concert_.name._meta.index, True)
        self.assertEqual(Concert_.name._meta.index_method, IndexMethod.hash)

        self.assertEqual(Concert_.time._meta.index, True)
        self.assertEqual(Concert_.time._meta.index_method, IndexMethod.btree)

        self.assertEqual(Concert_.capacity._meta.index, False)
        self.assertEqual(
            Concert_.capacity._meta.index_method, IndexMethod.btree
        )


###############################################################################


class Publication(Table, tablename="schema2.publication"):
    name = Varchar(length=50)


class Writer(Table, tablename="schema1.writer"):
    name = Varchar(length=50)
    publication = ForeignKey(Publication, null=True)


class Book(Table):
    name = Varchar(length=50)
    writer = ForeignKey(Writer, null=True)
    popularity = Integer(default=0)


@postgres_only
class TestGenerateWithSchema(TestCase):
    def setUp(self) -> None:
        engine: t.Optional[Engine] = engine_finder()

        class Schema(Table, db=engine):
            """
            Only for raw query execution
            """

            pass

        Schema.raw("CREATE SCHEMA IF NOT EXISTS schema1").run_sync()
        Schema.raw("CREATE SCHEMA IF NOT EXISTS schema2").run_sync()
        Publication.create_table().run_sync()
        Writer.create_table().run_sync()
        Book.create_table().run_sync()

    def tearDown(self) -> None:
        Book.alter().drop_table().run_sync()
        Writer.alter().drop_table().run_sync()
        Publication.alter().drop_table().run_sync()

    def test_reference_to_another_schema(self):
        output_schema: OutputSchema = run_sync(get_output_schema())
        self.assertEqual(len(output_schema.tables), 3)
        publication = output_schema.tables[0]
        writer = output_schema.tables[1]
        book = output_schema.tables[2]
        # Make sure referenced tables have been created
        self.assertEqual(
            Publication._meta.tablename, publication._meta.tablename
        )
        self.assertEqual(Writer._meta.tablename, writer._meta.tablename)

        # Make sure foreign key values are correct.
        self.assertEqual(writer.publication, publication)
        self.assertEqual(book.writer, writer)
