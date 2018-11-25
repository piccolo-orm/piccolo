from unittest import TestCase

from tests.example_project.tables import Band, Stadium, Concert


class TestGetRelated(TestCase):

    def setUp(self):
        Band.create().run_sync()
        Stadium.create().run_sync()
        Concert.create().run_sync()

    def tearDown(self):
        Concert.drop().run_sync()
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

        concert = Concert(
            band_1=pikachu.id,
            band_2=squirtle.id,
            stadium=stadium.id
        )
        concert.save().run_sync()

        _concert = Concert.objects().where(
            Concert.id == concert.id
        ).first().run_sync()

        _stadium = _concert.get_related('stadium').run_sync()

        self.assertTrue(
            _stadium.name == 'red stadium'
        )
