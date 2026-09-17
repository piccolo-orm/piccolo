from unittest import TestCase

from piccolo.columns import Varchar
from piccolo.query.functions.text_search import (
    Matches,
    PlainToTsQuery,
    ToTsQuery,
    ToTsVector,
    WebsearchToTsQuery,
)
from piccolo.table import Table
from piccolo.testing.test_case import AsyncTableTest
from tests.base import engines_only, engines_skip


class Band(Table):
    name = Varchar()


@engines_only("postgres")
class TestTextSearch(AsyncTableTest):

    tables = [Band]

    async def asyncSetUp(self):
        await super().asyncSetUp()

        await Band.insert(
            Band({Band.name: "Pythonistas play rock"}),
            Band({Band.name: "Rustaceans play jazz"}),
        )

    async def test_to_tsvector(self):
        response = await Band.select(
            ToTsVector(Band.name, config="simple")
        ).order_by(Band.name)

        self.assertListEqual(
            response,
            [
                {"to_tsvector": "'play':2 'pythonistas':1 'rock':3"},
                {"to_tsvector": "'jazz':3 'play':2 'rustaceans':1"},
            ],
        )

    async def test_matches(self):
        response = await Band.select(Band.name).where(
            Matches(
                ToTsVector(Band.name, config="english"),
                ToTsQuery("rock", config="english"),
            )
        )

        self.assertListEqual(response, [{"name": "Pythonistas play rock"}])

    async def test_to_tsquery_operators(self):
        """
        ``to_tsquery`` understands the full query syntax.
        """
        response = await Band.select(Band.name).where(
            Matches(
                ToTsVector(Band.name, config="english"),
                ToTsQuery("play & !rock", config="english"),
            )
        )

        self.assertListEqual(response, [{"name": "Rustaceans play jazz"}])

    async def test_plainto_tsquery(self):
        """
        Every word is combined with ``AND``.
        """
        response = await Band.select(Band.name).where(
            Matches(
                ToTsVector(Band.name, config="english"),
                PlainToTsQuery("play jazz", config="english"),
            )
        )

        self.assertListEqual(response, [{"name": "Rustaceans play jazz"}])

    async def test_websearch_to_tsquery(self):
        """
        Web search syntax - a quoted phrase, and ``-`` to exclude.
        """
        response = await Band.select(Band.name).where(
            Matches(
                ToTsVector(Band.name, config="english"),
                WebsearchToTsQuery("play -jazz", config="english"),
            )
        )

        self.assertListEqual(response, [{"name": "Pythonistas play rock"}])

    async def test_no_config(self):
        """
        The database's default config should be used.
        """
        response = await Band.select(Band.name).where(
            Matches(ToTsVector(Band.name), PlainToTsQuery("rock"))
        )

        self.assertListEqual(response, [{"name": "Pythonistas play rock"}])

    async def test_no_match(self):
        response = await Band.select(Band.name).where(
            Matches(
                ToTsVector(Band.name, config="english"),
                PlainToTsQuery("clarinet", config="english"),
            )
        )

        self.assertListEqual(response, [])


class TestTextSearchValidation(TestCase):

    @engines_only("postgres")
    def test_invalid_config(self):
        """
        The config is written into the query, so it must be an identifier.
        """
        for config in ("english'; DROP TABLE band; --", "en glish", ""):
            with self.assertRaises(ValueError):
                ToTsVector(Band.name, config=config)

    @engines_skip("postgres")
    def test_wrong_engine(self):
        """
        Full text search is Postgres only.
        """
        with self.assertRaises(ValueError) as manager:
            ToTsVector(Band.name)

        self.assertEqual(
            str(manager.exception),
            "Only Postgres supports full text search.",
        )
