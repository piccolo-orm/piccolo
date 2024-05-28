import sqlite3
from unittest import TestCase

import pytest

from piccolo.columns import Integer, Serial, Varchar
from piccolo.query.methods.insert import OnConflictAction
from piccolo.table import Table
from piccolo.utils.lazy_loader import LazyLoader
from tests.base import (
    DBTestCase,
    engine_version_lt,
    engines_only,
    is_running_sqlite,
)
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
        id: Serial
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
            target=Band.name,
            action="DO UPDATE",
            values=[Band.popularity],
        ).run_sync()

        self.assertListEqual(
            Band.select().run_sync(),
            [
                {
                    "id": self.band.id,
                    "name": self.band.name,
                    "popularity": new_popularity,  # changed
                }
            ],
        )

    def test_do_update_tuple_values(self):
        """
        Make sure we can use tuples in ``values``.
        """
        Band = self.Band

        new_popularity = self.band.popularity + 1000
        new_name = "Rustaceans"

        Band.insert(
            Band(
                id=self.band.id,
                name=new_name,
                popularity=new_popularity,
            )
        ).on_conflict(
            action="DO UPDATE",
            target=Band.id,
            values=[
                (Band.name, new_name),
                (Band.popularity, new_popularity + 2000),
            ],
        ).run_sync()

        self.assertListEqual(
            Band.select().run_sync(),
            [
                {
                    "id": self.band.id,
                    "name": new_name,
                    "popularity": new_popularity + 2000,
                }
            ],
        )

    def test_do_update_no_values(self):
        """
        Make sure that `DO UPDATE` with no `values` raises an exception.
        """
        Band = self.Band

        new_popularity = self.band.popularity + 1000

        with self.assertRaises(ValueError) as manager:
            Band.insert(
                Band(name=self.band.name, popularity=new_popularity)
            ).on_conflict(
                target=Band.name,
                action="DO UPDATE",
            ).run_sync()

        self.assertEqual(
            manager.exception.__str__(),
            "No values specified for `on conflict`",
        )

    @engines_only("postgres", "cockroach")
    def test_target_tuple(self):
        """
        Make sure that a composite unique constraint can be used as a target.

        We only run it on Postgres and Cockroach because we use ALTER TABLE
        to add a contraint, which SQLite doesn't support.
        """
        Band = self.Band

        # Add a composite unique constraint:
        Band.raw(
            "ALTER TABLE band ADD CONSTRAINT id_name_unique UNIQUE (id, name)"
        ).run_sync()

        Band.insert(
            Band(
                id=self.band.id,
                name=self.band.name,
                popularity=self.band.popularity,
            )
        ).on_conflict(
            target=(Band.id, Band.name),
            action="DO NOTHING",
        ).run_sync()

    @engines_only("postgres", "cockroach")
    def test_target_string(self):
        """
        Make sure we can explicitly specify the name of target constraint using
        a string.

        We just test this on Postgres for now, as we have to get the constraint
        name from the database.
        """
        Band = self.Band

        constraint_name = Band.raw(
            """
            SELECT constraint_name
            FROM information_schema.constraint_column_usage
            WHERE column_name = 'name'
                AND table_name = 'band';
            """
        ).run_sync()[0]["constraint_name"]

        query = Band.insert(Band(name=self.band.name)).on_conflict(
            target=constraint_name,
            action="DO NOTHING",
        )
        self.assertIn(f'ON CONSTRAINT "{constraint_name}"', query.__str__())
        query.run_sync()

    def test_violate_non_target(self):
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
                target=Band.id,  # Target the primary key instead.
                action="DO UPDATE",
                values=[Band.popularity],
            ).run_sync()

        if self.Band._meta.db.engine_type in ("postgres", "cockroach"):
            self.assertIsInstance(
                manager.exception, asyncpg.exceptions.UniqueViolationError
            )
        elif self.Band._meta.db.engine_type == "sqlite":
            self.assertIsInstance(manager.exception, sqlite3.IntegrityError)

    def test_where(self):
        """
        Make sure we can pass in a `where` argument.
        """
        Band = self.Band

        new_popularity = self.band.popularity + 1000

        query = Band.insert(
            Band(name=self.band.name, popularity=new_popularity)
        ).on_conflict(
            target=Band.name,
            action="DO UPDATE",
            values=[Band.popularity],
            where=Band.popularity < self.band.popularity,
        )

        self.assertIn(
            f'WHERE "band"."popularity" < {self.band.popularity}',
            query.__str__(),
        )

        query.run_sync()

    def test_do_nothing_where(self):
        """
        Make sure an error is raised if `where` is used with `DO NOTHING`.
        """
        Band = self.Band

        with self.assertRaises(ValueError) as manager:
            Band.insert(Band()).on_conflict(
                action="DO NOTHING",
                where=Band.popularity < self.band.popularity,
            )

        self.assertEqual(
            manager.exception.__str__(),
            "The `where` option can only be used with DO NOTHING.",
        )

    def test_do_nothing(self):
        """
        Make sure that `DO NOTHING` works.
        """
        Band = self.Band

        new_popularity = self.band.popularity + 1000

        Band.insert(
            Band(name="Pythonistas", popularity=new_popularity)
        ).on_conflict(action="DO NOTHING").run_sync()

        self.assertListEqual(
            Band.select().run_sync(),
            [
                {
                    "id": self.band.id,
                    "name": self.band.name,
                    "popularity": self.band.popularity,
                }
            ],
        )

    @engines_only("sqlite")
    def test_multiple_do_update(self):
        """
        Make sure multiple `ON CONFLICT` clauses work for SQLite.
        """
        Band = self.Band

        new_popularity = self.band.popularity + 1000

        # Conflicting with name - should update.
        Band.insert(
            Band(name="Pythonistas", popularity=new_popularity)
        ).on_conflict(action="DO NOTHING", target=Band.id).on_conflict(
            action="DO UPDATE", target=Band.name, values=[Band.popularity]
        ).run_sync()

        self.assertListEqual(
            Band.select().run_sync(),
            [
                {
                    "id": self.band.id,
                    "name": self.band.name,
                    "popularity": new_popularity,  # changed
                }
            ],
        )

    @engines_only("sqlite")
    def test_multiple_do_nothing(self):
        """
        Make sure multiple `ON CONFLICT` clauses work for SQLite.
        """
        Band = self.Band

        new_popularity = self.band.popularity + 1000

        # Conflicting with ID - should be ignored.
        Band.insert(
            Band(
                id=self.band.id,
                name="Pythonistas",
                popularity=new_popularity,
            )
        ).on_conflict(action="DO NOTHING", target=Band.id).on_conflict(
            action="DO UPDATE",
            target=Band.name,
            values=[Band.popularity],
        ).run_sync()

        self.assertListEqual(
            Band.select().run_sync(),
            [
                {
                    "id": self.band.id,
                    "name": self.band.name,
                    "popularity": self.band.popularity,
                }
            ],
        )

    @engines_only("postgres", "cockroach")
    def test_mutiple_error(self):
        """
        Postgres and Cockroach don't support multiple `ON CONFLICT` clauses.
        """
        with self.assertRaises(NotImplementedError) as manager:
            Band = self.Band

            Band.insert(Band()).on_conflict(action="DO NOTHING").on_conflict(
                action="DO UPDATE",
            ).run_sync()

        assert manager.exception.__str__() == (
            "Postgres and Cockroach only support a single ON CONFLICT clause."
        )

    def test_all_columns(self):
        """
        We can use ``all_columns`` instead of specifying the ``values``
        manually.
        """
        Band = self.Band

        new_popularity = self.band.popularity + 1000
        new_name = "Rustaceans"

        # Conflicting with ID - should be ignored.
        q = Band.insert(
            Band(
                id=self.band.id,
                name=new_name,
                popularity=new_popularity,
            )
        ).on_conflict(
            action="DO UPDATE",
            target=Band.id,
            values=Band.all_columns(),
        )
        q.run_sync()

        self.assertListEqual(
            Band.select().run_sync(),
            [
                {
                    "id": self.band.id,
                    "name": new_name,
                    "popularity": new_popularity,
                }
            ],
        )

    def test_enum(self):
        """
        A string literal can be passed in, or an enum, to determine the action.
        Make sure that the enum works.
        """
        Band = self.Band

        Band.insert(
            Band(
                id=self.band.id,
                name=self.band.name,
                popularity=self.band.popularity,
            )
        ).on_conflict(action=OnConflictAction.do_nothing).run_sync()

        self.assertListEqual(
            Band.select().run_sync(),
            [
                {
                    "id": self.band.id,
                    "name": self.band.name,
                    "popularity": self.band.popularity,
                }
            ],
        )
