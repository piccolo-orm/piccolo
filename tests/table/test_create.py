from unittest import TestCase
from ..example_project.tables import Manager


class TestCreate(TestCase):

    def test_create_table(self):
        Manager.create.run_sync()

        # Just do a count to make sure the table was created ok.
        count_query = Manager.select.count()
        response = count_query.run_sync()

        self.assertEqual(response[0]['count'], 0)

        Manager.drop.run_sync()
