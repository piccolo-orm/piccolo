from tests.example_project.tables import Band
from tests.base import DBTestCase


class TestDelete(DBTestCase):

    def setUp(self):
        Band.create.run_sync()

    def tearDown(self):
        Band.drop.run_sync()

    def test_delete(self):

        band = Band(
            name='Rubists',
            manager='Maz',
            popularity=300
        )

        band.save().run_sync()
        band.remove().run_sync()

        # how can I implement 'flat=True'
        # Band.select.columns(Band.name).output(as_list=True).run_sync()
        #
        Band.select.columns(Band.name).run_sync()
