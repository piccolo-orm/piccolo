from unittest import TestCase

from ..example_project.tables import Manager


class TestTableExists(TestCase):

    def setUp(self):
        Manager.create.run_sync()

    def test_table_exists(self):
        response = Manager.table_exists.run_sync()
        self.assertTrue(response is True)

    def tearDown(self):
        Manager.drop.run_sync()
