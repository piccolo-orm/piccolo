from unittest import TestCase

from piccolo.query.functions.string import Upper
from piccolo.table import create_db_tables_sync, drop_db_tables_sync
from tests.example_apps.music.tables import Band, Manager


class TestUpperFunction(TestCase):

    tables = (Band, Manager)

    def setUp(self) -> None:
        create_db_tables_sync(*self.tables)

        manager = Manager({Manager.name: "Guido"})
        manager.save().run_sync()

        band = Band({Band.name: "Pythonistas", Band.manager: manager})
        band.save().run_sync()

    def tearDown(self) -> None:
        drop_db_tables_sync(*self.tables)

    def test_column(self):
        """
        Make sure we can uppercase a column's value.
        """
        response = Band.select(Upper(Band.name)).run_sync()
        self.assertEqual(response, [{"upper": "PYTHONISTAS"}])

    def test_alias(self):
        response = Band.select(Upper(Band.name, alias="name")).run_sync()
        self.assertEqual(response, [{"name": "PYTHONISTAS"}])

    def test_joined_column(self):
        """
        Make sure we can uppercase a column's value from a joined table.
        """
        response = Band.select(Upper(Band.manager._.name)).run_sync()
        self.assertEqual(response, [{"upper": "GUIDO"}])
