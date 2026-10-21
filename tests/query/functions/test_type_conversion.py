from unittest import TestCase

from piccolo.columns import BigInt, Integer, Text, Varchar
from piccolo.engine.postgres import PostgresEngine
from piccolo.engine.sqlite import SQLiteEngine
from piccolo.query.functions import Cast, Length
from piccolo.table import create_table_class
from tests.example_apps.music.tables import Band, Manager

from .base import BandTest


class TestCast(BandTest):
    def test_varchar(self):
        """
        Make sure that casting to ``Varchar`` works.
        """
        response = Band.select(
            Cast(
                Band.popularity,
                as_type=Varchar(),
            )
        ).run_sync()

        self.assertListEqual(
            response,
            [{"popularity": "1000"}],
        )

    def test_text(self):
        """
        Make sure that casting to ``Text`` works.
        """
        response = Band.select(
            Cast(
                Band.popularity,
                as_type=Text(),
            )
        ).run_sync()

        self.assertListEqual(
            response,
            [{"popularity": "1000"}],
        )

    def test_integer(self):
        """
        Make sure that casting to ``Integer`` works.
        """
        Band.update({Band.name: "1111"}, force=True).run_sync()

        response = Band.select(
            Cast(
                Band.name,
                as_type=Integer(),
            )
        ).run_sync()

        self.assertListEqual(
            response,
            [{"name": 1111}],
        )

    def test_join(self):
        """
        Make sure that casting works with joins.
        """
        Manager.update({Manager.name: "1111"}, force=True).run_sync()

        response = Band.select(
            Band.name,
            Cast(
                Band.manager.name,
                as_type=Integer(),
            ),
        ).run_sync()

        self.assertListEqual(
            response,
            [
                {
                    "name": "Pythonistas",
                    "manager.name": 1111,
                }
            ],
        )

    def test_nested_inner(self):
        """
        Make sure ``Cast`` can be passed into other functions.
        """
        Band.update({Band.name: "1111"}, force=True).run_sync()

        response = Band.select(
            Length(
                Cast(
                    Band.popularity,
                    as_type=Varchar(),
                )
            )
        ).run_sync()

        self.assertListEqual(
            response,
            [{"length": 4}],
        )

    def test_nested_outer(self):
        """
        Make sure a querystring can be passed into ``Cast`` (meaning it can be
        nested).
        """
        response = Band.select(
            Cast(
                Length(Band.name),
                as_type=Varchar(),
                alias="length",
            )
        ).run_sync()

        self.assertListEqual(
            response,
            [{"length": str(len("Pythonistas"))}],
        )

    def test_where_clause(self):
        """
        Make sure ``Cast`` works in a where clause.
        """
        response = (
            Band.select(Band.name, Band.popularity)
            .where(Cast(Band.popularity, Varchar()) == "1000")
            .run_sync()
        )

        self.assertListEqual(
            response,
            [{"name": "Pythonistas", "popularity": 1000}],
        )


class TestCastTable(TestCase):
    def test_existing_table(self):
        """
        If the ``as_type`` column already has a table, and the identifier
        doesn't give us one, then the existing table should be used to work
        out the column type.
        """
        sqlite_table = create_table_class(
            "SQLiteTable", class_kwargs={"db": SQLiteEngine()}
        )
        postgres_table = create_table_class(
            "PostgresTable", class_kwargs={"db": PostgresEngine(config={})}
        )

        for table, expected in (
            (sqlite_table, "CAST(1 AS INTEGER)"),
            (postgres_table, "CAST(1 AS BIGINT)"),
        ):
            with self.subTest(table=table):
                as_type = BigInt()
                as_type._meta.table = table
                self.assertEqual(str(Cast(1, as_type=as_type)), expected)
