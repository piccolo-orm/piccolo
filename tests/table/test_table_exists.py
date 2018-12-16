from unittest import TestCase

from ..example_project.tables import Band


class TestTableExists(TestCase):

    def setUp(self):
        Band.create.run_sync()

    def test_table_exists(self):
        response = Band.table_exists.run_sync()
        self.assertTrue(response is True)

    def tearDown(self):
        Band.drop.run_sync()
