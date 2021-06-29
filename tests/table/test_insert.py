from ..base import DBTestCase
from ..example_app.tables import Band, Manager


class TestInsert(DBTestCase):
    def test_insert(self):
        self.insert_rows()

        Band.insert(Band(name="Rustaceans", popularity=100)).run_sync()

        response = Band.select(Band.name).run_sync()
        names = [i["name"] for i in response]

        self.assertTrue("Rustaceans" in names)

    def test_add(self):
        self.insert_rows()

        Band.insert().add(Band(name="Rustaceans", popularity=100)).run_sync()

        response = Band.select(Band.name).run_sync()
        names = [i["name"] for i in response]

        self.assertTrue("Rustaceans" in names)

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

        self.assertTrue("{}" in names)
