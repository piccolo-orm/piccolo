from dataclasses import dataclass
import timeit
import typing as t
from unittest.mock import patch

from piccolo.query.base import Query

from tests.base import DBTestCase
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
            QueryResponse(
                query=(
                    Band.select(Band.name)
                    .where(Band.name == "Pythonistas")
                    .output(as_json=True)
                    .freeze()
                ),
                response='[{"name":"Pythonistas"}]',
            ),
        ]

        for query_response in query_responses:
            result = query_response.query.run_sync()
            self.assertEqual(result, query_response.response)

    # def test_frozen_performance(self):
    #     """
    #     The frozen query performance should exceed the non-frozen. If not,
    #     there's a problem.
    #     """
    #     with patch.object(Band._meta.db, "run_querystring"):
    #         pass

    #     iterations = 50
    #     query = Band.select().where(Band.name == "Pythonistas").first()
    #     query_duration = timeit.timeit(
    #         lambda: query.run_sync(), number=iterations
    #     )

    #     # patch out the actual database call ... patching the engine is
    #     # quite challenging ...

    #     frozen_query = query.freeze()
    #     frozen_query_duration = timeit.timeit(
    #         lambda: frozen_query.run_sync(), number=iterations
    #     )
    #     self.assertTrue(query_duration > frozen_query_duration)

    # def test_attribute_access(self):
    #     pass
