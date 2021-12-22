import decimal
from unittest import TestCase

from piccolo.table import create_tables, drop_tables
from tests.example_apps.music.tables import (
    Band,
    Concert,
    Manager,
    Ticket,
    Venue,
)

TABLES = [Band, Concert, Manager, Venue, Ticket]


class TestGetRelatedReadable(TestCase):
    def setUp(self):
        create_tables(*TABLES)

        manager_1 = Manager.objects().create(name="Guido").run_sync()
        manager_2 = Manager.objects().create(name="Graydon").run_sync()

        band_1 = (
            Band.objects()
            .create(name="Pythonistas", manager=manager_1)
            .run_sync()
        )
        band_2 = (
            Band.objects()
            .create(name="Rustaceans", manager=manager_2)
            .run_sync()
        )
        venue = (
            Venue.objects()
            .create(name="Royal Albert Hall", capacity=5900)
            .run_sync()
        )
        concert = (
            Concert.objects()
            .create(venue=venue, band_1=band_1, band_2=band_2)
            .run_sync()
        )
        Ticket.objects().create(
            price=decimal.Decimal(50.0), concert=concert
        ).run_sync()

    def tearDown(self):
        drop_tables(*TABLES)

    def test_get_related_readable(self):
        """
        Make sure you can get the `Readable` representation for related object
        from another object instance.
        """
        response = Band.select(
            Band.name, Band._get_related_readable(Band.manager)
        ).run_sync()

        self.assertEqual(
            response,
            [
                {"name": "Pythonistas", "manager_readable": "Guido"},
                {"manager_readable": "Graydon", "name": "Rustaceans"},
            ],
        )

        # Now try something much more complex.
        response = Ticket.select(
            Ticket.id, Ticket._get_related_readable(Ticket.concert)
        ).run_sync()
        self.assertEqual(
            response,
            [
                {
                    "id": 1,
                    "concert_readable": (
                        "Pythonistas and Rustaceans at Royal Albert Hall, "
                        "capacity 5900"
                    ),
                }
            ],
        )
