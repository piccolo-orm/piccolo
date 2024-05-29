from unittest import TestCase

from piccolo.query.functions.string import Reverse, Upper
from piccolo.querystring import QueryString
from piccolo.table import create_db_tables_sync, drop_db_tables_sync
from tests.base import engines_skip
from tests.example_apps.music.tables import Band, Manager


class FunctionTest(TestCase):
    tables = (Band, Manager)

    def setUp(self) -> None:
        create_db_tables_sync(*self.tables)

        manager = Manager({Manager.name: "Guido"})
        manager.save().run_sync()

        band = Band({Band.name: "Pythonistas", Band.manager: manager})
        band.save().run_sync()

    def tearDown(self) -> None:
        drop_db_tables_sync(*self.tables)


class TestUpperFunction(FunctionTest):

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


@engines_skip("sqlite")
class TestNested(FunctionTest):
    """
    Skip the the test for SQLite, as it doesn't support ``Reverse``.
    """

    def test_nested(self):
        """
        Make sure we can nest functions.
        """
        response = Band.select(Upper(Reverse(Band.name))).run_sync()
        self.assertListEqual(response, [{"upper": "SATSINOHTYP"}])

    def test_nested_with_joined_column(self):
        """
        Make sure nested functions can be used on a column from a joined table.
        """
        response = Band.select(Upper(Reverse(Band.manager._.name))).run_sync()
        self.assertListEqual(response, [{"upper": "ODIUG"}])

    def test_nested_within_querystring(self):
        """
        If we wrap a function in a custom QueryString - make sure the columns
        are still accessible, so joins are successful.
        """
        response = Band.select(
            QueryString("CONCAT({}, '!')", Upper(Band.manager._.name)),
        ).run_sync()

        self.assertListEqual(response, [{"concat": "GUIDO!"}])


class TestWhereClause(FunctionTest):

    def test_where(self):
        """
        Make sure where clauses work with functions.
        """
        response = (
            Band.select(Band.name)
            .where(Upper(Band.name) == "PYTHONISTAS")
            .run_sync()
        )
        self.assertListEqual(response, [{"name": "Pythonistas"}])

    def test_where_with_joined_column(self):
        """
        Make sure where clauses work with functions, when a joined column is
        used.
        """
        response = (
            Band.select(Band.name)
            .where(Upper(Band.manager._.name) == "GUIDO")
            .run_sync()
        )
        self.assertListEqual(response, [{"name": "Pythonistas"}])
