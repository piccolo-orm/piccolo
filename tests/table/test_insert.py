import sqlite3
from unittest import TestCase

import pytest

from piccolo.columns import Integer, Varchar
from piccolo.table import Table
from piccolo.utils.lazy_loader import LazyLoader
from tests.base import DBTestCase, engine_version_lt, is_running_sqlite
from tests.example_apps.music.tables import Band, Manager

asyncpg = LazyLoader("asyncpg", globals(), "asyncpg")


class TestInsert(DBTestCase):
    def test_insert(self):
        self.insert_rows()

        Band.insert(Band(name="Rustaceans", popularity=100)).run_sync()

        response = Band.select(Band.name).run_sync()
        names = [i["name"] for i in response]

        self.assertIn("Rustaceans", names)

    def test_add(self):
        self.insert_rows()

        Band.insert().add(Band(name="Rustaceans", popularity=100)).run_sync()

        response = Band.select(Band.name).run_sync()
        names = [i["name"] for i in response]

        self.assertIn("Rustaceans", names)

    def test_incompatible_type(self):
        """
        You shouldn't be able to add instances of a different table.
        """
        with self.assertRaises(TypeError):
            Band.insert().add(Manager(name="Guido")).run_sync()

    def test_insert_curly_braces(self):
        """
        You should be able to insert curly braces without an error.
        """
        self.insert_rows()

        Band.insert(Band(name="{}", popularity=100)).run_sync()

        response = Band.select(Band.name).run_sync()
        names = [i["name"] for i in response]

        self.assertIn("{}", names)

    @pytest.mark.skipif(
        is_running_sqlite() and engine_version_lt(3.35),
        reason="SQLite version not supported",
    )
    def test_insert_returning(self):
        """
        Make sure update works with the `returning` clause.
        """
        response = (
            Manager.insert(Manager(name="Maz"))
            .returning(Manager.name)
            .run_sync()
        )

        self.assertListEqual(response, [{"name": "Maz"}])

    @pytest.mark.skipif(
        is_running_sqlite() and engine_version_lt(3.35),
        reason="SQLite version not supported",
    )
    def test_insert_returning_alias(self):
        """
        Make sure update works with the `returning` clause.
        """
        response = (
            Manager.insert(Manager(name="Maz"))
            .returning(Manager.name.as_alias("manager_name"))
            .run_sync()
        )

        self.assertListEqual(response, [{"manager_name": "Maz"}])


@pytest.mark.skipif(
    is_running_sqlite() and engine_version_lt(3.24),
    reason="SQLite version not supported",
)
class TestOnConflict(TestCase):
    class Band(Table):
        name = Varchar(unique=True)
        popularity = Integer()

    def setUp(self) -> None:
        Band = self.Band
        Band.create_table().run_sync()
        self.band = Band({Band.name: "Pythonistas", Band.popularity: 1000})
        self.band.save().run_sync()

    def tearDown(self) -> None:
        Band = self.Band
        Band.alter().drop_table().run_sync()

    def test_do_update(self):
        """
        Make sure that `DO UPDATE` works.
        """
        Band = self.Band

        new_popularity = self.band.popularity + 1000

        Band.insert(
            Band(name=self.band.name, popularity=new_popularity)
        ).on_conflict(
            targets=[Band.name],
            action="DO UPDATE",
            values=[Band.popularity],
        ).run_sync()

        self.assertListEqual(
            Band.select(Band.name, Band.popularity).run_sync(),
            [{"name": self.band.name, "popularity": new_popularity}],
        )

    def test_non_target(self):
        """
        Make sure that if we specify a target constraint, but violate a
        different constraint, then we still get the error.
        """
        Band = self.Band

        new_popularity = self.band.popularity + 1000

        with self.assertRaises(Exception) as manager:
            Band.insert(
                Band(name=self.band.name, popularity=new_popularity)
            ).on_conflict(
                targets=[Band.id],  # Target the primary key instead.
                action="DO UPDATE",
                values=[Band.popularity],
            ).run_sync()

        if self.Band._meta.db.engine_type in ("postgres", "cockroach"):
            self.assertIsInstance(
                manager.exception, asyncpg.exceptions.UniqueViolationError
            )
        elif self.Band._meta.db.engine_type == "sqlite":
            self.assertIsInstance(manager.exception, sqlite3.IntegrityError)

    def test_do_nothing(self):
        """
        Make sure that `DO NOTHING` works.
        """
        Band = self.Band

        Band.insert(Band(name="Pythonistas", popularity=5000)).on_conflict(
            action="DO NOTHING"
        ).run_sync()

        self.assertListEqual(
            Band.select(Band.name, Band.popularity).run_sync(),
            [{"name": self.band.name, "popularity": self.band.popularity}],
        )
