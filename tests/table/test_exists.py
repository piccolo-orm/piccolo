from ..base import DBTestCase
from ..example_app.tables import Band


class TestExists(DBTestCase):
    def test_exists(self):
        self.insert_rows()

        response = Band.exists().where(Band.name == "Pythonistas").run_sync()

        self.assertTrue(response is True)
