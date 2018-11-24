from tests.example_project.tables import Band
from tests.base import DBTestCase


class TestDelete(DBTestCase):

    def setUp(self):
        Band.create().run_sync()

    def tearDown(self):
        Band.drop().run_sync()

    def test_delete(self):

        squirtle = Band(
            name='squirtle',
            trainer='Misty',
            power=300
        )

        squirtle.save().run_sync()
        squirtle.remove().run_sync()

        # how can I implement 'flat=True'
        # Band.select('name').output(as_list=True).run_sync()
        #
        Band.select('name').run_sync()
