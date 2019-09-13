from ..base import DBTestCase
from ..example_project.tables import Band, Concert


class TestRaw(DBTestCase):
    def test_raw_without_args(self):
        self.insert_row()

        response = Band.raw("select * from band").run_sync()

        self.assertDictEqual(
            response[0],
            {"id": 1, "name": "Pythonistas", "manager": 1, "popularity": 1000},
        )

    def test_raw_with_args(self):
        self.insert_rows()

        response = Band.raw(
            "select * from band where name = {}", "Pythonistas"
        ).run_sync()

        self.assertTrue(len(response) == 1)
        self.assertDictEqual(
            response[0],
            {"id": 1, "name": "Pythonistas", "manager": 1, "popularity": 1000},
        )
