from unittest import TestCase

from ..example_project.tables import Band, Venue, Concert


class TestCreateJoin():

    def test_create_join(self):

        Band.create.run_sync()
        Venue.create.run_sync()
        Concert.create.run_sync()

        Concert.drop.run_sync()
        Band.drop.run_sync()
        Venue.drop.run_sync()


class TestJoin(TestCase):
    """
    Test instantiating Table instances
    """

    def setUp(self):
        Band.create.run_sync()
        Venue.create.run_sync()
        Concert.create.run_sync()

    def tearDown(self):
        Concert.drop.run_sync()
        Band.drop.run_sync()
        Venue.drop.run_sync()

    def test_join(self):
        Pythonistas = Band(name="Pythonistas", manager="Guido")
        Pythonistas.save().run_sync()

        band = Band(name="Rustaceans")
        band.save().run_sync()

        venue = Venue(name="Grand Central")
        venue.save().run_sync()

        # TODO - make sure you can also do:
        # band_1=Pythonistas
        save_query = Concert(
            band_1=Pythonistas.id,
            band_2=band.id,
            venue=venue.id
        ).save()
        save_query.run_sync()

        select_query = Concert.select.columns(
            Concert.band_1.name,
            Concert.band_2.name,
            Concert.venue.name,
            Concert.band_1.manager
        )
        response = select_query.run_sync()
        print(response)

    # def _test_ref(self):
    #     """
    #     Concert.select().count().where(
    #         Concert.ref('band1.name') == 'Pythonistas'
    #     )
    #     """
    #     pass
