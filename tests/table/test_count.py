from tests.base import DBTestCase
from tests.example_apps.music.tables import Band


class TestCount(DBTestCase):
    def test_exists(self):
        self.insert_rows()

        response = Band.count().where(Band.name == "Pythonistas").run_sync()

        self.assertEqual(response, 1)
