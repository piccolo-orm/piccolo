from unittest import TestCase

from ..example_project.tables import Pokemon


class TestTableExists(TestCase):

    def setUp(self):
        Pokemon.create().run_sync()

    def test_table_exists(self):
        response = Pokemon.table_exists().run_sync()
        self.assertTrue(response is True)

    def tearDown(self):
        Pokemon.drop().run_sync()
