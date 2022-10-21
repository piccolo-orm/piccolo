import pytest

from tests.base import DBTestCase, engine_version_lt, is_running_sqlite
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
