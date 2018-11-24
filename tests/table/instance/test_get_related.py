from unittest import TestCase

from tests.example_project.tables import Band, Stadium, Match


class TestGetRelated(TestCase):

    def setUp(self):
        Band.create().run_sync()
        Stadium.create().run_sync()
        Match.create().run_sync()

    def tearDown(self):
        Match.drop().run_sync()
        Band.drop().run_sync()
        Stadium.drop().run_sync()

    def test_get_related(self):
        """
        Make sure you can get a related object from another object instance.
        """
        pikachu = Band(
            name='pikachu'
        )
        pikachu.save().run_sync()

        squirtle = Band(
            name='squirtle'
        )
        squirtle.save().run_sync()

        stadium = Stadium(
            name="red stadium"
        )
        stadium.save().run_sync()

        match = Match(
            band_1=pikachu.id,
            band_2=squirtle.id,
            stadium=stadium.id
        )
        match.save().run_sync()

        _match = Match.objects().where(
            Match.id == match.id
        ).first().run_sync()

        _stadium = _match.get_related('stadium').run_sync()

        self.assertTrue(
            _stadium.name == 'red stadium'
        )
