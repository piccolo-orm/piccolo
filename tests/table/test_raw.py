from piccolo.query.base import Query
from piccolo.querystring import QueryString
from tests.base import DBTestCase, engine_is
from tests.example_apps.music.tables import Band


class TestRaw(DBTestCase):
    def test_raw_without_args(self):
        self.insert_row()

        response = Band.raw("SELECT * FROM band").run_sync()

        if engine_is("cockroach"):
            self.assertDictEqual(
                response[0],
                {
                    "id": response[0]["id"],
                    "name": "Pythonistas",
                    "manager": response[0]["manager"],
                    "popularity": 1000,
                },
            )
        else:
            self.assertDictEqual(
                response[0],
                {
                    "id": 1,
                    "name": "Pythonistas",
                    "manager": 1,
                    "popularity": 1000,
                },
            )

    def test_raw_with_args(self):
        self.insert_rows()

        response = Band.raw(
            "SELECT * FROM band WHERE name = {}", "Pythonistas"
        ).run_sync()

        self.assertEqual(len(response), 1)

        if engine_is("cockroach"):
            self.assertDictEqual(
                response[0],
                {
                    "id": response[0]["id"],
                    "name": "Pythonistas",
                    "manager": response[0]["manager"],
                    "popularity": 1000,
                },
            )
        else:
            self.assertDictEqual(
                response[0],
                {
                    "id": 1,
                    "name": "Pythonistas",
                    "manager": 1,
                    "popularity": 1000,
                },
            )


class TestRawQueryString(DBTestCase):
    def test_querystring(self):
        self.insert_rows()

        response = Band.raw(
            QueryString("SELECT name FROM band WHERE name = {}", "Rustaceans")
        ).run_sync()

        self.assertListEqual(response, [{"name": "Rustaceans"}])

    def test_querystring_with_args(self):
        with self.assertRaises(ValueError):
            Band.raw(QueryString("SELECT * FROM band"), "Pythonistas")

    def test_nested_query(self):
        """
        A query can be nested within a ``QueryString``.
        """
        self.insert_rows()

        query = Band.select(Band.name).where(Band.name == "Rustaceans")
        response = Band.raw(
            QueryString("SELECT COUNT(*) AS total FROM ({}) AS sub", query)
        ).run_sync()

        self.assertListEqual(response, [{"total": 1}])

    def test_nested_query_multiple_statements(self):
        with self.assertRaises(ValueError):
            QueryString(
                "{}",
                Query(
                    Band,
                    frozen_querystrings=[
                        QueryString("SELECT 1"),
                        QueryString("SELECT 2"),
                    ],
                ),
            )
