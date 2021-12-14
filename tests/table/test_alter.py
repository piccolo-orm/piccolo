from __future__ import annotations

import typing as t
from unittest import TestCase

from piccolo.columns import BigInt, Integer, Numeric, Varchar
from piccolo.columns.base import Column
from piccolo.columns.column_types import ForeignKey, Text
from piccolo.table import Table
from tests.base import DBTestCase, postgres_only
from tests.example_apps.music.tables import Band, Manager


class TestRenameColumn(DBTestCase):
    def _test_rename(
        self,
        existing_column: t.Union[Column, str],
        new_column_name: str = "rating",
    ):
        self.insert_row()

        rename_query = Band.alter().rename_column(
            existing_column, new_column_name
        )
        rename_query.run_sync()

        select_query = Band.raw("SELECT * FROM band")
        response = select_query.run_sync()

        column_names = response[0].keys()
        existing_column_name = (
            existing_column._meta.name
            if isinstance(existing_column, Column)
            else existing_column
        )
        self.assertTrue(
            (new_column_name in column_names)
            and (existing_column_name not in column_names)
        )

    def test_column(self):
        """
        Make sure a ``Column`` argument works.
        """
        self._test_rename(Band.popularity)

    def test_string(self):
        """
        Make sure a string argument works.
        """
        self._test_rename("popularity")

    def test_problematic_name(self):
        """
        Make sure we can rename columns with names which clash with SQL
        keywords.
        """
        self._test_rename(
            existing_column=Band.popularity, new_column_name="order"
        )


class TestRenameTable(DBTestCase):
    def test_rename(self):
        Band.alter().rename_table("act").run_sync()
        self.assertEqual(Band.raw("SELECT * FROM act").run_sync(), [])

    def tearDown(self):
        super().tearDown()
        self.run_sync("DROP TABLE IF EXISTS act")


@postgres_only
class TestDropColumn(DBTestCase):
    """
    Unfortunately this only works with Postgres at the moment.

    SQLite has very limited support for ALTER statements.
    """

    def _test_drop(self, column: str):
        self.insert_row()

        Band.alter().drop_column(column).run_sync()

        response = Band.raw("SELECT * FROM band").run_sync()

        column_names = response[0].keys()
        self.assertTrue("popularity" not in column_names)

    def test_drop_string(self):
        self._test_drop(Band.popularity)

    def test_drop_column(self):
        self._test_drop("popularity")


class TestAddColumn(DBTestCase):
    def _test_add_column(
        self, column: Column, column_name: str, expected_value: t.Any
    ):
        self.insert_row()
        Band.alter().add_column(column_name, column).run_sync()

        response = Band.raw("SELECT * FROM band").run_sync()

        column_names = response[0].keys()
        self.assertTrue(column_name in column_names)

        self.assertEqual(response[0][column_name], expected_value)

    def test_integer(self):
        self._test_add_column(
            column=Integer(null=True, default=None),
            column_name="members",
            expected_value=None,
        )

    def test_foreign_key(self):
        self._test_add_column(
            column=ForeignKey(references=Manager),
            column_name="assistant_manager",
            expected_value=None,
        )

    def test_text(self):
        bio = "An amazing band"
        self._test_add_column(
            column=Text(default=bio),
            column_name="bio",
            expected_value=bio,
        )

    def test_problematic_name(self):
        """
        Make sure we can add columns with names which clash with SQL keywords.
        """
        self._test_add_column(
            column=Text(default="asc"),
            column_name="order",
            expected_value="asc",
        )


@postgres_only
class TestUnique(DBTestCase):
    def test_unique(self):
        unique_query = Manager.alter().set_unique(Manager.name, True)
        unique_query.run_sync()

        Manager(name="Bob").save().run_sync()

        # Make sure non-unique names work:
        Manager(name="Sally").save().run_sync()

        # Check there's a unique row error ...
        with self.assertRaises(Exception):
            Manager(name="Bob").save().run_sync()

        response = Manager.select().run_sync()
        self.assertTrue(len(response) == 2)

        # Now remove the constraint, and add a row.
        not_unique_query = Manager.alter().set_unique(Manager.name, False)
        not_unique_query.run_sync()
        Manager(name="Bob").save().run_sync()

        response = Manager.select().run_sync()
        self.assertTrue(len(response), 2)


@postgres_only
class TestMultiple(DBTestCase):
    """
    Make sure multiple alter statements work correctly.
    """

    def test_multiple(self):
        self.insert_row()

        query = (
            Manager.alter()
            .add_column("column_a", Integer(default=0, null=True))
            .add_column("column_b", Integer(default=0, null=True))
        )
        query.run_sync()

        response = Band.raw("SELECT * FROM manager").run_sync()

        column_names = response[0].keys()
        self.assertTrue("column_a" in column_names)
        self.assertTrue("column_b" in column_names)


# TODO - test more conversions.
@postgres_only
class TestSetColumnType(DBTestCase):
    def test_integer_to_bigint(self):
        """
        Test converting an Integer column to BigInt.
        """
        self.insert_row()

        alter_query = Band.alter().set_column_type(
            old_column=Band.popularity, new_column=BigInt()
        )
        alter_query.run_sync()

        self.assertEqual(
            self.get_postgres_column_type(
                tablename="band", column_name="popularity"
            ),
            "BIGINT",
        )

        popularity = (
            Band.select(Band.popularity).first().run_sync()["popularity"]
        )
        self.assertEqual(popularity, 1000)

    def test_integer_to_varchar(self):
        """
        Test converting an Integer column to Varchar.
        """
        self.insert_row()

        alter_query = Band.alter().set_column_type(
            old_column=Band.popularity, new_column=Varchar()
        )
        alter_query.run_sync()

        self.assertEqual(
            self.get_postgres_column_type(
                tablename="band", column_name="popularity"
            ),
            "CHARACTER VARYING",
        )

        popularity = (
            Band.select(Band.popularity).first().run_sync()["popularity"]
        )
        self.assertEqual(popularity, "1000")

    def test_using_expression(self):
        """
        Test the `using_expression` option, which can be used to tell Postgres
        how to convert certain column types.
        """
        Band(name="1").save().run_sync()

        alter_query = Band.alter().set_column_type(
            old_column=Band.name,
            new_column=Integer(),
            using_expression="name::integer",
        )
        alter_query.run_sync()

        popularity = Band.select(Band.name).first().run_sync()["name"]
        self.assertEqual(popularity, 1)


@postgres_only
class TestSetNull(DBTestCase):
    def test_set_null(self):
        query = """
            SELECT is_nullable FROM information_schema.columns
            WHERE table_name = 'band'
            AND table_catalog = 'piccolo'
            AND column_name = 'popularity'
            """

        Band.alter().set_null(Band.popularity, boolean=True).run_sync()
        response = Band.raw(query).run_sync()
        self.assertTrue(response[0]["is_nullable"] == "YES")

        Band.alter().set_null(Band.popularity, boolean=False).run_sync()
        response = Band.raw(query).run_sync()
        self.assertTrue(response[0]["is_nullable"] == "NO")


@postgres_only
class TestSetLength(DBTestCase):
    def test_set_length(self):
        query = """
            SELECT character_maximum_length FROM information_schema.columns
            WHERE table_name = 'band'
            AND table_catalog = 'piccolo'
            AND column_name = 'name'
            """

        for length in (5, 20, 50):
            Band.alter().set_length(Band.name, length=length).run_sync()
            response = Band.raw(query).run_sync()
            self.assertTrue(response[0]["character_maximum_length"] == length)


@postgres_only
class TestSetDefault(DBTestCase):
    def test_set_default(self):
        Manager.alter().set_default(Manager.name, "Pending").run_sync()

        # Bypassing the ORM to make sure the database default is present.
        Band.raw(
            "INSERT INTO manager (id, name) VALUES (DEFAULT, DEFAULT);"
        ).run_sync()

        manager = Manager.objects().first().run_sync()
        self.assertTrue(manager.name == "Pending")


###############################################################################


class Ticket(Table):
    price = Numeric(digits=(5, 2))


@postgres_only
class TestSetDigits(TestCase):
    def setUp(self):
        Ticket.create_table().run_sync()

    def tearDown(self):
        Ticket.alter().drop_table().run_sync()

    def test_set_digits(self):
        query = """
            SELECT numeric_precision, numeric_scale
            FROM information_schema.columns
            WHERE table_name = 'ticket'
            AND table_catalog = 'piccolo'
            AND column_name = 'price'
            """

        Ticket.alter().set_digits(
            column=Ticket.price, digits=(6, 2)
        ).run_sync()
        response = Ticket.raw(query).run_sync()
        self.assertTrue(response[0]["numeric_precision"] == 6)
        self.assertTrue(response[0]["numeric_scale"] == 2)

        Ticket.alter().set_digits(column=Ticket.price, digits=None).run_sync()
        response = Ticket.raw(query).run_sync()
        self.assertTrue(response[0]["numeric_precision"] is None)
        self.assertTrue(response[0]["numeric_scale"] is None)
