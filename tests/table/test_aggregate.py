from piccolo.query import Avg, Max, Min, Sum

from ..base import DBTestCase
from ..example_app.tables import Band


class TestAggregate(DBTestCase):
    def test_avg(self):
        self.insert_rows()

        response = Band.select(Avg(Band.popularity)).first().run_sync()

        self.assertTrue(float(response["avg"]) == 1003.3333333333334)

    def test_max(self):
        self.insert_rows()

        response = Band.select(Max(Band.popularity)).first().run_sync()

        self.assertTrue(response["max"] == 2000)

    def test_min(self):
        self.insert_rows()

        response = Band.select(Min(Band.popularity)).first().run_sync()

        self.assertTrue(response["min"] == 10)

    def test_sum(self):
        self.insert_rows()

        response = Band.select(Sum(Band.popularity)).first().run_sync()

        self.assertTrue(response["sum"] == 3010)

    def test_chain_different_functions(self):
        self.insert_rows()

        response = (
            Band.select(Avg(Band.popularity), Sum(Band.popularity))
            .first()
            .run_sync()
        )

        self.assertTrue(float(response["avg"]) == 1003.3333333333334)
        self.assertTrue(response["sum"] == 3010)

    def test_avg_validation(self):
        with self.assertRaises(Exception):
            Band.select(Avg(Band.name)).run_sync()

    def test_sum_validation(self):
        with self.assertRaises(Exception):
            Band.select(Sum(Band.name)).run_sync()
