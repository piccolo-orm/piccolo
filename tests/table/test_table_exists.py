from unittest import TestCase

from tests.example_apps.music.tables import Manager


class TestTableExists(TestCase):
    def setUp(self):
        Manager.create_table().run_sync()

    def test_table_exists(self):
        response = Manager.table_exists().run_sync()
        self.assertTrue(response is True)

    def tearDown(self):
        Manager.alter().drop_table().run_sync()
