import decimal
from unittest import TestCase

from tests.example_apps.music.tables import (
    Band,
    Concert,
    Manager,
    Ticket,
    Venue,
)

TABLES = [Manager, Band, Venue, Concert]


class TestCreateJoin:
    def test_create_join(self):
        for table in TABLES:
            table.create_table().run_sync()

        for table in reversed(TABLES):
            table.alter().drop_table().run_sync()


class TestJoin(TestCase):

    tables = [Manager, Band, Venue, Concert, Ticket]

    def setUp(self):
        for table in self.tables:
            table.create_table().run_sync()

        manager_1 = Manager(name="Guido")
        manager_1.save().run_sync()

        band_1 = Band(
            name="Pythonistas", manager=manager_1.id, popularity=1000
        )
        band_1.save().run_sync()

        manager_2 = Manager(name="Graydon")
        manager_2.save().run_sync()

        band_2 = Band(name="Rustaceans", manager=manager_2.id)
        band_2.save().run_sync()

        venue = Venue(name="Grand Central", capacity=1000)
        venue.save().run_sync()

        concert = Concert(band_1=band_1.id, band_2=band_2.id, venue=venue.id)
        concert.save().run_sync()

        ticket = Ticket(concert=concert, price=decimal.Decimal(50.0))
        ticket.save().run_sync()

    def tearDown(self):
        for table in reversed(self.tables):
            table.alter().drop_table().run_sync()

    ###########################################################################

    def test_join(self):
        select_query = Concert.select(
            Concert.band_1.name,
            Concert.band_2.name,
            Concert.venue.name,
            Concert.band_1.manager,
        )
        response = select_query.run_sync()
        self.assertEqual(
            response,
            [
                {
                    "band_1.name": "Pythonistas",
                    "band_2.name": "Rustaceans",
                    "venue.name": "Grand Central",
                    "band_1.manager": 1,
                }
            ],
        )

        # Now make sure that even deeper joins work:
        select_query = Concert.select(Concert.band_1.manager.name)
        response = select_query.run_sync()
        self.assertEqual(response, [{"band_1.manager.name": "Guido"}])

    def test_select_all_columns(self):
        """
        Make sure you can retrieve all columns from a related table, without
        explicitly specifying them.
        """
        result = (
            Band.select(Band.name, Band.manager.all_columns())
            .first()
            .run_sync()
        )
        self.assertDictEqual(
            result,
            {
                "name": "Pythonistas",
                "manager.id": 1,
                "manager.name": "Guido",
            },
        )

    def test_select_all_columns_deep(self):
        """
        Make sure that ``all_columns`` can be used several layers deep.
        """
        result = (
            Concert.select(
                Concert.venue.all_columns(),
                Concert.band_1.manager.all_columns(),
                Concert.band_2.manager.all_columns(),
            )
            .first()
            .run_sync()
        )

        self.assertDictEqual(
            result,
            {
                "venue.id": 1,
                "venue.name": "Grand Central",
                "venue.capacity": 1000,
                "band_1.manager.id": 1,
                "band_1.manager.name": "Guido",
                "band_2.manager.id": 2,
                "band_2.manager.name": "Graydon",
            },
        )

    def test_select_all_columns_root(self):
        """
        Make sure that using ``all_columns`` at the root doesn't interfere
        with using it for referenced tables.
        """
        result = (
            Band.select(
                Band.all_columns(),
                Band.manager.all_columns(),
            )
            .first()
            .run_sync()
        )
        self.assertDictEqual(
            result,
            {
                "id": 1,
                "name": "Pythonistas",
                "manager": 1,
                "popularity": 1000,
                "manager.id": 1,
                "manager.name": "Guido",
            },
        )

    def test_select_all_columns_root_nested(self):
        """
        Make sure that using ``all_columns`` at the root doesn't interfere
        with using it for referenced tables.
        """
        result = (
            Band.select(Band.all_columns(), Band.manager.all_columns())
            .output(nested=True)
            .first()
            .run_sync()
        )

        self.assertDictEqual(
            result,
            {
                "id": 1,
                "name": "Pythonistas",
                "manager": {"id": 1, "name": "Guido"},
                "popularity": 1000,
            },
        )

    def test_select_all_columns_exclude(self):
        """
        Make sure we can get all columns, except the ones we specify.
        """
        result = (
            Band.select(
                Band.all_columns(exclude=[Band.id]),
                Band.manager.all_columns(exclude=[Band.manager.id]),
            )
            .output(nested=True)
            .first()
            .run_sync()
        )

        result_str_args = (
            Band.select(
                Band.all_columns(exclude=["id"]),
                Band.manager.all_columns(exclude=["id"]),
            )
            .output(nested=True)
            .first()
            .run_sync()
        )

        for data in (result, result_str_args):
            self.assertDictEqual(
                data,
                {
                    "name": "Pythonistas",
                    "manager": {"name": "Guido"},
                    "popularity": 1000,
                },
            )

    ###########################################################################

    def test_objects_nested(self):
        """
        Make sure the prefetch argument works correctly for objects.
        """
        band = Band.objects(Band.manager).first().run_sync()
        self.assertIsInstance(band.manager, Manager)

    def test_objects__all_related__root(self):
        """
        Make sure that ``all_related`` works correctly when called from the
        root table of the query.
        """
        concert = Concert.objects(Concert.all_related()).first().run_sync()
        self.assertIsInstance(concert.band_1, Band)
        self.assertIsInstance(concert.band_2, Band)
        self.assertIsInstance(concert.venue, Venue)

    def test_objects_nested_deep(self):
        """
        Make sure that ``prefetch`` works correctly with deeply nested tables.
        """
        ticket = (
            Ticket.objects(
                Ticket.concert,
                Ticket.concert.band_1,
                Ticket.concert.band_2,
                Ticket.concert.venue,
                Ticket.concert.band_1.manager,
                Ticket.concert.band_2.manager,
            )
            .first()
            .run_sync()
        )

        self.assertIsInstance(ticket.concert, Concert)
        self.assertIsInstance(ticket.concert.band_1, Band)
        self.assertIsInstance(ticket.concert.band_2, Band)
        self.assertIsInstance(ticket.concert.venue, Venue)
        self.assertIsInstance(ticket.concert.band_1.manager, Manager)
        self.assertIsInstance(ticket.concert.band_2.manager, Manager)

    def test_objects__all_related__deep(self):
        """
        Make sure that ``all_related`` works correctly when called on a deeply
        nested table.
        """
        ticket = (
            Ticket.objects(
                Ticket.all_related(),
                Ticket.concert.all_related(),
                Ticket.concert.band_1.all_related(),
                Ticket.concert.band_2.all_related(),
            )
            .first()
            .run_sync()
        )

        self.assertIsInstance(ticket.concert, Concert)
        self.assertIsInstance(ticket.concert.band_1, Band)
        self.assertIsInstance(ticket.concert.band_2, Band)
        self.assertIsInstance(ticket.concert.venue, Venue)
        self.assertIsInstance(ticket.concert.band_1.manager, Manager)
        self.assertIsInstance(ticket.concert.band_2.manager, Manager)

    def test_objects_prefetch_clause(self):
        """
        Make sure that ``prefetch`` clause works correctly.
        """
        ticket = (
            Ticket.objects()
            .prefetch(
                Ticket.all_related(),
                Ticket.concert.all_related(),
                Ticket.concert.band_1.all_related(),
                Ticket.concert.band_2.all_related(),
            )
            .first()
            .run_sync()
        )

        self.assertIsInstance(ticket.concert, Concert)
        self.assertIsInstance(ticket.concert.band_1, Band)
        self.assertIsInstance(ticket.concert.band_2, Band)
        self.assertIsInstance(ticket.concert.venue, Venue)
        self.assertIsInstance(ticket.concert.band_1.manager, Manager)
        self.assertIsInstance(ticket.concert.band_2.manager, Manager)

    def test_objects_prefetch_intermediate(self):
        """
        Make sure when using ``prefetch`` on a deeply nested table, all of the
        intermediate objects are also retrieved properly.
        """
        ticket = (
            Ticket.objects()
            .prefetch(
                Ticket.concert.band_1.manager,
            )
            .first()
            .run_sync()
        )

        self.assertIsInstance(ticket.price, decimal.Decimal)
        self.assertIsInstance(ticket.concert, Concert)

        self.assertIsInstance(ticket.concert.id, int)
        self.assertIsInstance(ticket.concert.band_1, Band)
        self.assertIsInstance(ticket.concert.band_2, int)
        self.assertIsInstance(ticket.concert.venue, int)

        self.assertIsInstance(ticket.concert.band_1.id, int)
        self.assertIsInstance(ticket.concert.band_1.name, str)
        self.assertIsInstance(ticket.concert.band_1.manager, Manager)

        self.assertIsInstance(ticket.concert.band_1.manager.id, int)
        self.assertIsInstance(ticket.concert.band_1.manager.name, str)

    def test_objects_prefetch_multiple_intermediate(self):
        """
        Make sure that if we're fetching multiple deeply nested tables, the
        intermediate tables are still created correctly.
        """
        ticket = (
            Ticket.objects()
            .prefetch(
                Ticket.concert.band_1.manager,
                Ticket.concert.band_2.manager,
            )
            .first()
            .run_sync()
        )

        self.assertIsInstance(ticket.price, decimal.Decimal)
        self.assertIsInstance(ticket.concert, Concert)

        self.assertIsInstance(ticket.concert.id, int)
        self.assertIsInstance(ticket.concert.band_1, Band)
        self.assertIsInstance(ticket.concert.band_2, Band)
        self.assertIsInstance(ticket.concert.venue, int)

        self.assertIsInstance(ticket.concert.band_1.id, int)
        self.assertIsInstance(ticket.concert.band_1.name, str)
        self.assertIsInstance(ticket.concert.band_1.manager, Manager)

        self.assertIsInstance(ticket.concert.band_1.manager.id, int)
        self.assertIsInstance(ticket.concert.band_1.manager.name, str)

        self.assertIsInstance(ticket.concert.band_2.id, int)
        self.assertIsInstance(ticket.concert.band_2.name, str)
        self.assertIsInstance(ticket.concert.band_2.manager, Manager)

        self.assertIsInstance(ticket.concert.band_2.manager.id, int)
        self.assertIsInstance(ticket.concert.band_2.manager.name, str)
