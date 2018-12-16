from unittest import TestCase

from tests.example_project.tables import Band, Venue, Concert


class TestGetRelated(TestCase):

    def setUp(self):
        Band.create.run_sync()
        Venue.create.run_sync()
        Concert.create.run_sync()

    def tearDown(self):
        Concert.drop.run_sync()
        Band.drop.run_sync()
        Venue.drop.run_sync()

    def test_get_related(self):
        """
        Make sure you can get a related object from another object instance.
        """
        Pythonistas = Band(
            name='Pythonistas'
        )
        Pythonistas.save().run_sync()

        rubists = Band(
            name='Rubists'
        )
        rubists.save().run_sync()

        venue = Venue(
            name="red venue"
        )
        venue.save().run_sync()

        concert = Concert(
            band_1=Pythonistas.id,
            band_2=rubists.id,
            venue=venue.id
        )
        concert.save().run_sync()

        _concert = Concert.objects.where(
            Concert.id == concert.id
        ).first().run_sync()

        _venue = _concert.get_related('venue').run_sync()

        self.assertTrue(
            _venue.name == 'red venue'
        )
