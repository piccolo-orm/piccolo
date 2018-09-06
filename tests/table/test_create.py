from ..base import DBTestCase
from ..example_project.tables import Pokemon


class TestCreate(DBTestCase):

    def setUp(self):
        """
        Need to override, otherwise table will be auto created.
        """
        pass

    def test_create_table(self):
        Pokemon.create().run_sync()

        # Just do a count to make sure the table was created ok.
        response = Pokemon.select(
            'name', 'trainer', 'power'
        ).count().run_sync()

        self.assertEqual(response[0]['count'], 0)
