from tests.example_apps.music.tables import Band, Manager

from ..base import DBTestCase


class TestInsert(DBTestCase):
    def test_insert(self):
        self.test_insert_curly_braces_2("Rustaceans")

    def test_add(self):
        self.insert_rows()

        Band.insert().add(Band(name="Rustaceans", popularity=100)).run_sync()

        self.test_insert_curly_braces_2_1("Rustaceans")

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
        self.test_insert_curly_braces_2("{}")

    # TODO Rename this here and in `test_insert` and `test_insert_curly_braces`
    def test_insert_curly_braces_2(self, name):
        self.insert_rows()
        Band.insert(Band(name=name, popularity=100)).run_sync()
        self.test_insert_curly_braces_2_1(name)

    # TODO Rename this here and in `test_add` and `test_insert_curly_braces_2`
    def test_insert_curly_braces_2_1(self, arg0):
        response = Band.select(Band.name).run_sync()
        names = [i["name"] for i in response]
        self.assertTrue(arg0 in names)
