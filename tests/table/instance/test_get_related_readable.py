import decimal
from unittest import TestCase

from piccolo.columns import ForeignKey, Varchar
from piccolo.columns.readable import Readable
from piccolo.table import Table, create_db_tables_sync, drop_db_tables_sync
from tests.base import engine_is
from tests.example_apps.music.tables import (
    Band,
    Concert,
    Manager,
    Ticket,
    Venue,
)


class ThingOne(Table):
    name = Varchar(length=300, null=False)


class ThingTwo(Table):
    name = Varchar(length=300, null=False)
    thing_one = ForeignKey(references=ThingOne)


class ThingThree(Table):
    name = Varchar(length=300, null=False)
    thing_two = ForeignKey(references=ThingTwo)

    @classmethod
    def get_readable(cls):
        return Readable(
            template="three name: %s - two name: %s - one name: %s",
            columns=[
                cls.name,
                cls.thing_two.name,
                cls.thing_two.thing_one.name,
            ],
        )


class ThingFour(Table):
    name = Varchar(length=300, null=False)
    thing_three = ForeignKey(references=ThingThree)


TABLES = [
    Band,
    Concert,
    Manager,
    Venue,
    Ticket,
    ThingOne,
    ThingTwo,
    ThingThree,
    ThingFour,
]


class TestGetRelatedReadable(TestCase):
    def setUp(self):
        create_db_tables_sync(*TABLES)

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

        thing_one = ThingOne.insert(ThingOne(name="thing_one")).run_sync()
        thing_two = ThingTwo.insert(
            ThingTwo(name="thing_two", thing_one=thing_one[0]["id"])
        ).run_sync()
        thing_three = ThingThree.insert(
            ThingThree(name="thing_three", thing_two=thing_two[0]["id"])
        ).run_sync()
        ThingFour.insert(
            ThingFour(name="thing_four", thing_three=thing_three[0]["id"])
        ).run_sync()

    def tearDown(self):
        drop_db_tables_sync(*TABLES)

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
            Ticket.id,
            Ticket._get_related_readable(Ticket.concert),
        ).run_sync()

        if engine_is("cockroach"):
            self.assertEqual(
                response,
                [
                    {
                        "id": response[0]["id"],
                        "concert_readable": (
                            "Pythonistas and Rustaceans at Royal Albert Hall, "
                            "capacity 5900"
                        ),
                    }
                ],
            )
        else:
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

        # A really complex references chain from Piccolo Admin issue #170
        response = ThingFour.select(
            ThingFour._get_related_readable(ThingFour.thing_three)
        ).run_sync()
        self.assertEqual(
            response,
            [
                {
                    "thing_three_readable": (
                        "three name: thing_three - two name: thing_two - one name: thing_one"  # noqa: E501
                    )
                }
            ],
        )
