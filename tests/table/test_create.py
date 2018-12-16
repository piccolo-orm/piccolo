from ..base import DBTestCase
from ..example_project.tables import Band


class TestCreate(DBTestCase):

    def setUp(self):
        """
        Need to override, otherwise table will be auto created.
        """
        pass

    def test_create_table(self):
        Band.create.run_sync()

        # Just do a count to make sure the table was created ok.
        response = Band.select.columns(
            Band.name, Band.manager, Band.popularity
        ).count().run_sync()

        self.assertEqual(response[0]['count'], 0)
