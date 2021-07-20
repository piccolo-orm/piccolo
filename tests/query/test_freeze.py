import timeit
import typing as t
from dataclasses import dataclass

from piccolo.query.base import Query
from tests.base import DBTestCase, sqlite_only
from tests.example_app.tables import Band


@dataclass
class QueryResponse:
    query: Query
    response: t.Any


class TestFreeze(DBTestCase):
    def test_frozen_select_queries(self):
        """
        Make sure a variety of select queries work as expected when frozen.
        """
        self.insert_rows()

        query_responses: t.List[QueryResponse] = [
            QueryResponse(
                query=(
                    Band.select(Band.name)
                    .order_by(Band.popularity, ascending=False)
                    .first()
                    .freeze()
                ),
                response={"name": "Rustaceans"},
            ),
            QueryResponse(
                query=(
                    Band.select(Band.name)
                    .order_by(Band.popularity, ascending=False)
                    .freeze()
                ),
                response=[
                    {"name": "Rustaceans"},
                    {"name": "Pythonistas"},
                    {"name": "CSharps"},
                ],
            ),
            QueryResponse(
                query=(
                    Band.select(Band.name)
                    .where(Band.name == "Pythonistas")
                    .freeze()
                ),
                response=[{"name": "Pythonistas"}],
            ),
        ]

        for query_response in query_responses:
            result = query_response.query.run_sync()
            self.assertEqual(result, query_response.response)

    def test_output_clause(self):
        """
        Make sure the output clause still works correctly with frozen queries.
        """
        self.insert_rows()

        result = (
            Band.select(Band.name)
            .where(Band.name == "Pythonistas")
            .output(as_json=True)
            .freeze()
            .run_sync()
        )
        # Some JSON encoders have a space after the colons and some don't,
        # so normalise them.
        self.assertEqual(result.replace(" ", ""), '[{"name":"Pythonistas"}]')

    @sqlite_only
    def test_frozen_performance(self):
        """
        The frozen query performance should exceed the non-frozen. If not,
        there's a problem.

        Only test this on SQLite, as the latency from the database itself
        is more predictable than with Postgres, and the test runs quickly.

        """
        iterations = 50
        query = Band.select().where(Band.name == "Pythonistas").first()
        query_duration = timeit.repeat(
            lambda: query.run_sync(), repeat=iterations, number=1
        )

        frozen_query = query.freeze()
        frozen_query_duration = timeit.repeat(
            lambda: frozen_query.run_sync(), repeat=iterations, number=1
        )

        # Remove the outliers before comparing
        self.assertTrue(
            sum(sorted(query_duration)[5:-5])
            > sum(sorted(frozen_query_duration)[5:-5])
        )

    def test_attribute_access(self):
        """
        Once frozen, you shouldn't be able to call additional methods on the
        query (for example `.where`).
        """
        query = Band.select().freeze()

        with self.assertRaises(AttributeError):
            query.where(Band.name == "Pythonistas")
