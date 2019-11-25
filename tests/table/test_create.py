from unittest import TestCase
from ..example_project.tables import Manager


class TestCreate(TestCase):
    def test_create_table(self):
        Manager.create_table().run_sync()

        # Just do a count to make sure the table was created ok.
        count_query = Manager.count()
        response = count_query.run_sync()

        self.assertEqual(response, 0)

        Manager.alter().drop_table().run_sync()
