import ast
from unittest import TestCase

from piccolo.columns.column_types import Varchar
from piccolo.constraints import Check, Unique
from piccolo.query.methods.alter import AddForeignKeyConstraint
from piccolo.schema import SchemaManager
from piccolo.table import Table
from piccolo.utils.escaping import escape_sql_literal, quote_ident


class Band(Table):
    name = Varchar()


class TestEscapeSQLLiteral(TestCase):
    def test_single_quotes(self):
        """
        Single quotes should be doubled, so a value can't break out of a
        string literal.
        """
        self.assertEqual(escape_sql_literal("O'Brien"), "O''Brien")
        self.assertEqual(
            escape_sql_literal("x'; DROP TABLE band; --"),
            "x''; DROP TABLE band; --",
        )

    def test_no_op(self):
        self.assertEqual(escape_sql_literal("hello world"), "hello world")

    def test_array_element(self):
        """
        Inside a Postgres array literal, elements are double quoted, and
        backslashes / double quotes are backslash escaped.
        """
        self.assertEqual(escape_sql_literal('a"b', delimiter='"'), 'a\\"b')
        self.assertEqual(escape_sql_literal("a\\b", delimiter='"'), "a\\\\b")

        # The backslash must be escaped first, otherwise we'd escape our own
        # escapes.
        self.assertEqual(escape_sql_literal('\\"', delimiter='"'), '\\\\\\"')

    def test_empty_delimiter(self):
        """
        With no delimiter there's no quoting context to break out of.
        """
        self.assertEqual(escape_sql_literal("a'b", delimiter=""), "a'b")


class TestQuoteIdent(TestCase):
    def test_simple(self):
        self.assertEqual(quote_ident("name"), '"name"')

    def test_double_quotes(self):
        """
        Double quotes should be doubled, so an identifier can't break out and
        alter the surrounding SQL.
        """
        self.assertEqual(
            quote_ident('a" , (SELECT 1) AS "b'),
            '"a"" , (SELECT 1) AS ""b"',
        )

    def test_null_byte(self):
        """
        A NULL byte can truncate the statement, and no engine accepts it in an
        identifier.
        """
        with self.assertRaises(ValueError):
            quote_ident("a\x00b")


class TestNoInjection(TestCase):
    """
    Each of these used to allow a value to escape its quoting and modify the
    surrounding SQL.
    """

    def test_set_default(self):
        ddl = Band.alter().set_default(Band.name, "x'; DROP TABLE band; --")
        self.assertEqual(
            ddl.ddl[0],
            'ALTER TABLE "band" ALTER COLUMN "name" SET DEFAULT '
            "'x''; DROP TABLE band; --'",
        )

    def test_column_default(self):
        class Evil(Table):
            name = Varchar(default="x'); DROP TABLE band; --")

        self.assertIn(
            "DEFAULT 'x''); DROP TABLE band; --'",
            Evil.name.ddl,
        )

    def test_alias(self):
        querystring = Band.select(
            Band.name.as_alias('a" , (SELECT 1) AS "b')
        ).querystrings[0]
        self.assertIn(
            'AS "a"" , (SELECT 1) AS ""b"',
            querystring.compile_string(engine_type="postgres")[0],
        )

    def test_returning_alias(self):
        querystring = (
            Band.insert(Band(name="x"))
            .returning(Band.name.as_alias('a"b'))
            .querystrings[0]
        )
        self.assertIn(
            'RETURNING "name" AS "a""b"',
            querystring.compile_string(engine_type="postgres")[0],
        )

    def test_check_constraint(self):
        self.assertEqual(
            Check(Band.name == "x' OR '1'='1").ddl,
            "CHECK (\"name\" = 'x'' OR ''1''=''1')",
        )

    def test_unique_ddl(self):
        class Weird(Table):
            name = Varchar(db_column_name='we"ird')
            u = Unique([name])

        self.assertEqual(
            Weird._meta.constraints[0].ddl,
            'UNIQUE ("we""ird")',
        )

    def test_tablename_and_column_ddl(self):
        class Weird(Table, tablename='we"ird'):
            name = Varchar(db_column_name='co"l')

        self.assertEqual(Weird._meta.get_formatted_tablename(), '"we""ird"')
        self.assertIn('"co""l" VARCHAR', Weird.name.ddl)

    def test_select_full_name(self):
        class Weird(Table, tablename='we"ird'):
            name = Varchar(db_column_name='co"l')

        self.assertEqual(
            Weird.select(Weird.name)
            .querystrings[0]
            .compile_string(engine_type="postgres")[0],
            'SELECT ALL "we""ird"."co""l" AS "co""l" FROM "we""ird"',
        )

    def test_foreign_key_constraint(self):
        self.assertEqual(
            AddForeignKeyConstraint(
                constraint_name='c"1',
                foreign_key_column_name='f"k',
                referenced_table_name='t"bl',
                referenced_column_name='i"d',
                on_delete=None,
                on_update=None,
            ).ddl,
            'ADD CONSTRAINT "c""1" FOREIGN KEY ("f""k") '
            'REFERENCES "t""bl" ("i""d")',
        )

    def test_schema_name(self):
        manager = SchemaManager()

        self.assertEqual(
            manager.create_schema('tenant" ; --', if_not_exists=True).ddl,
            'CREATE SCHEMA IF NOT EXISTS "tenant"" ; --"',
        )
        self.assertEqual(
            manager.drop_schema('tenant" CASCADE --', if_exists=True).ddl,
            'DROP SCHEMA IF EXISTS "tenant"" CASCADE --"',
        )
        self.assertEqual(
            manager.rename_schema('a"b', 'c"d').ddl,
            'ALTER SCHEMA "a""b" RENAME TO "c""d"',
        )
        self.assertEqual(
            manager.move_table(
                table_name='t"1', new_schema='s"2', current_schema='s"3'
            ).ddl,
            'ALTER TABLE "s""3"."t""1" SET SCHEMA "s""2"',
        )


class TestConstraintCodegen(TestCase):
    """
    ``_table_str`` outputs Python source, so the values must be escaped with
    ``repr``, otherwise the generated code doesn't parse.
    """

    def _get_line(self, table: type[Table], prefix: str) -> str:
        return next(
            line.strip()
            for line in str(table).splitlines()
            if line.strip().startswith(prefix)
        )

    def test_check_parses(self):
        class Ticket(Table):
            name = Varchar()
            constraint = Check(name != "O'Brien")

        line = self._get_line(Ticket, "constraint =")
        self.assertEqual(
            line, "constraint = Check('\"name\" != \\'O\\'\\'Brien\\'')"
        )
        ast.parse(line)

    def test_unique_parses(self):
        class Ticket(Table):
            name = Varchar(db_column_name='we"ird')
            constraint = Unique([name])

        line = self._get_line(Ticket, "constraint =")
        self.assertEqual(
            line, "constraint = Unique(['we\"ird'], nulls_distinct=True)"
        )
        ast.parse(line)
