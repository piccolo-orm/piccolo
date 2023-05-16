from tests.base import DBTestCase, engines_only
from tests.example_apps.music.tables import Band


class TestCount(DBTestCase):
    def test_exists(self):
        self.insert_rows()

        response = Band.count().where(Band.popularity == 10).run_sync()

        self.assertEqual(response, 2)

    @engines_only("postgres", "cockroach")
    def test_count_distinct(self):
        self.insert_rows()

        response = Band.count().distinct(on=[Band.popularity]).run_sync()

        self.assertEqual(response, 3)
