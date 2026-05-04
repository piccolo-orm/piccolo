import pytest

from piccolo.query.functions.string import Concat, Upper
from tests.base import engine_version_lt, is_running_sqlite
from tests.example_apps.music.tables import Band

from .base import BandTest


class TestUpper(BandTest):

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


@pytest.mark.skipif(
    is_running_sqlite() and engine_version_lt(3.44),
    reason="SQLite version not supported",
)
class TestConcat(BandTest):

    def test_column_and_string(self):
        response = Band.select(
            Concat(Band.name, "!!!", alias="name")
        ).run_sync()
        self.assertListEqual(response, [{"name": "Pythonistas!!!"}])

    def test_column_and_column(self):
        response = Band.select(
            Concat(Band.name, Band.popularity, alias="name")
        ).run_sync()
        self.assertListEqual(response, [{"name": "Pythonistas1000"}])

    def test_join(self):
        response = Band.select(
            Concat(Band.name, "-", Band.manager._.name, alias="name")
        ).run_sync()
        self.assertListEqual(response, [{"name": "Pythonistas-Guido"}])

    def test_min_args(self):
        with self.assertRaises(ValueError):
            Concat()
