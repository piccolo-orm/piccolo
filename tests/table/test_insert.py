import pytest

from piccolo.query.mixins import OnConflict
from tests.base import (
    DBTestCase,
    engine_version_lt,
    engines_only,
    is_running_sqlite,
)
from tests.example_apps.music.tables import Band, Manager


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

    @engines_only("postgres", "sqlite")
    def test_insert_on_conflict_do_nothing(self):
        """
        Check that the record has not changed because of the
        `on_conflict` clause.
        """
        self.insert_rows()

        Band.insert(
            Band(id=1, name="Javas", popularity=100),
            on_conflict=OnConflict.do_nothing,
        ).run_sync()

        response = (
            Band.select(Band.name).where(Band.id == 1).first().run_sync()
        )
        self.assertEqual(response["name"], "Pythonistas")

    @engines_only("postgres", "sqlite")
    def test_insert_on_conflict_do_update_single_column(self):
        """
        Check that the record has changed because of the
        `on_update` clause.
        """
        self.insert_rows()

        Band.insert(
            Band(id=1, name="Pythonstas-updated", manager=1, popularity=1000),
            Band(id=2, name="Rustaceans-updated", manager=2, popularity=2000),
            Band(id=3, name="CSharps-updated", manager=3, popularity=10),
            on_conflict=OnConflict.do_update,
        ).run_sync()

        response = Band.select().run_sync()
        self.assertEqual(
            response,
            [
                {
                    "id": 1,
                    "name": "Pythonstas-updated",
                    "manager": 1,
                    "popularity": 1000,
                },
                {
                    "id": 2,
                    "name": "Rustaceans-updated",
                    "manager": 2,
                    "popularity": 2000,
                },
                {
                    "id": 3,
                    "name": "CSharps-updated",
                    "manager": 3,
                    "popularity": 10,
                },
            ],
        )

    @engines_only("postgres", "sqlite")
    def test_insert_on_conflict_do_update_multiple_columns(self):
        """
        Check that the record has changed because of the
        `on_update` clause.
        """
        self.insert_rows()

        Band.insert(
            Band(id=1, name="Pythonstas-updated", manager=3, popularity=200),
            Band(id=2, name="Rustaceans-updated", manager=2, popularity=1000),
            Band(id=3, name="CSharps-updated", manager=1, popularity=20),
            on_conflict=OnConflict.do_update,
        ).run_sync()

        response = Band.select().run_sync()
        self.assertEqual(
            response,
            [
                {
                    "id": 1,
                    "name": "Pythonstas-updated",
                    "manager": 3,
                    "popularity": 200,
                },
                {
                    "id": 2,
                    "name": "Rustaceans-updated",
                    "manager": 2,
                    "popularity": 1000,
                },
                {
                    "id": 3,
                    "name": "CSharps-updated",
                    "manager": 1,
                    "popularity": 20,
                },
            ],
        )

    @engines_only("cockroach")
    def test_insert_on_conflict_do_nothing_cockroach(self):
        """
        Check that the record has not changed because of the
        `on_conflict` clause.
        """
        self.insert_rows()

        results = Band.select().run_sync()

        Band.insert(
            Band(
                id=results[0]["id"],
                name="Javas",
                manager=results[0]["manager"],
                popularity=100,
            ),
            on_conflict=OnConflict.do_nothing,
        ).run_sync()

        response = (
            Band.select(Band.name)
            .where(Band.id == results[0]["id"])
            .first()
            .run_sync()
        )
        self.assertEqual(response["name"], "Pythonistas")

    @engines_only("cockroach")
    def test_insert_on_conflict_do_update_single_column_cockroach(self):
        """
        Check that the record has changed because of the
        `on_update` clause.
        """
        self.insert_rows()

        results = Band.select().run_sync()

        Band.insert(
            Band(
                id=results[0]["id"],
                name="Pythonstas-updated",
                manager=results[0]["manager"],
                popularity=1000,
            ),
            Band(
                id=results[1]["id"],
                name="Rustaceans-updated",
                manager=results[1]["manager"],
                popularity=2000,
            ),
            Band(
                id=results[2]["id"],
                name="CSharps-updated",
                manager=results[2]["manager"],
                popularity=10,
            ),
            on_conflict=OnConflict.do_update,
        ).run_sync()

        response = Band.select().run_sync()

        self.assertEqual(
            response,
            [
                {
                    "id": results[0]["id"],
                    "name": "Pythonstas-updated",
                    "manager": results[0]["manager"],
                    "popularity": 1000,
                },
                {
                    "id": results[1]["id"],
                    "name": "Rustaceans-updated",
                    "manager": results[1]["manager"],
                    "popularity": 2000,
                },
                {
                    "id": results[2]["id"],
                    "name": "CSharps-updated",
                    "manager": results[2]["manager"],
                    "popularity": 10,
                },
            ],
        )

    @engines_only("cockroach")
    def test_insert_on_conflict_do_update_multiple_columns_cockroach(self):
        """
        Check that the record has changed because of the
        `on_update` clause.
        """
        self.insert_rows()

        results = Band.select().run_sync()

        Band.insert(
            Band(
                id=results[0]["id"],
                name="Pythonstas-updated",
                manager=results[2]["manager"],
                popularity=200,
            ),
            Band(
                id=results[1]["id"],
                name="Rustaceans-updated",
                manager=results[1]["manager"],
                popularity=1000,
            ),
            Band(
                id=results[2]["id"],
                name="CSharps-updated",
                manager=results[0]["manager"],
                popularity=20,
            ),
            on_conflict=OnConflict.do_update,
        ).run_sync()

        response = Band.select().run_sync()
        self.assertEqual(
            response,
            [
                {
                    "id": results[0]["id"],
                    "name": "Pythonstas-updated",
                    "manager": results[2]["manager"],
                    "popularity": 200,
                },
                {
                    "id": results[1]["id"],
                    "name": "Rustaceans-updated",
                    "manager": results[1]["manager"],
                    "popularity": 1000,
                },
                {
                    "id": results[2]["id"],
                    "name": "CSharps-updated",
                    "manager": results[0]["manager"],
                    "popularity": 20,
                },
            ],
        )

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
