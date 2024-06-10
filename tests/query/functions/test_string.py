from piccolo.query.functions.string import Upper
from tests.example_apps.music.tables import Band

from .base import BandTest


class TestUpperFunction(BandTest):

    def test_column(self):
        """
        Make sure we can uppercase a column's value.
        """
        response = Band.select(Upper(Band.name)).run_sync()
        self.assertListEqual(response, [{"upper": "PYTHONISTAS"}])

    def test_alias(self):
        response = Band.select(Upper(Band.name, alias="name")).run_sync()
        self.assertListEqual(response, [{"name": "PYTHONISTAS"}])

    def test_joined_column(self):
        """
        Make sure we can uppercase a column's value from a joined table.
        """
        response = Band.select(Upper(Band.manager._.name)).run_sync()
        self.assertListEqual(response, [{"upper": "GUIDO"}])
