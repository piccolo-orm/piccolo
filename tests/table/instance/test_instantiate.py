from tests.base import DBTestCase, postgres_only, sqlite_only
from tests.example_app.tables import Band


class TestInstance(DBTestCase):
    """
    Test instantiating Table instances
    """

    @postgres_only
    def test_insert_postgres(self):
        Pythonistas = Band(name="Pythonistas")
        self.assertEqual(
            Pythonistas.__str__(), "(DEFAULT,'Pythonistas',null,0)"
        )

    @sqlite_only
    def test_insert_sqlite(self):
        Pythonistas = Band(name="Pythonistas")
        self.assertEqual(Pythonistas.__str__(), "(null,'Pythonistas',null,0)")

    def test_non_existant_column(self):
        with self.assertRaises(ValueError):
            Band(name="Pythonistas", foo="bar")
