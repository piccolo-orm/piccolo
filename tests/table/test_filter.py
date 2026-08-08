import datetime
from unittest import TestCase

from piccolo.columns.column_types import (
    ForeignKey,
    Integer,
    Timestamp,
    Varchar,
)
from piccolo.table import Table
from piccolo.testing.test_case import TableTest
from tests.base import DBTestCase
from tests.example_apps.music.tables import Band


class Event(Table):
    """
    ``year`` shares its name with a transform, so it's used to check that a
    column wins over a transform.
    """

    name = Varchar()
    year = Integer()
    starts = Timestamp()


class Ticket(Table):
    """
    Used to check that ``event__year`` resolves to ``Event.year`` rather than
    ``Year(Ticket.event)``.
    """

    event = ForeignKey(Event)


class Room(Table):
    """
    ``lt`` shares its name with an operator, so it's used to check that a
    column wins over an operator.
    """

    name = Varchar()
    lt = Integer()


class Booking(Table):
    room = ForeignKey(Room)


class Employee(Table):
    """
    Self-referencing, so a lookup can walk far enough to hit Piccolo's call
    chain limit.
    """

    name = Varchar()
    boss: ForeignKey["Employee"] = ForeignKey(references="Employee")


class TestFilter(DBTestCase):
    def test_equals(self):
        self.insert_rows()

        response = Band.filter(name="Pythonistas").run_sync()

        self.assertEqual([band.name for band in response], ["Pythonistas"])

    def test_no_criteria_returns_all(self):
        self.insert_rows()

        response = Band.filter().run_sync()

        self.assertEqual(len(response), 3)

    def test_gte(self):
        self.insert_rows()

        response = (
            Band.filter(popularity__gte=1000).order_by(Band.name).run_sync()
        )

        self.assertEqual(
            [band.name for band in response], ["Pythonistas", "Rustaceans"]
        )

    def test_lt(self):
        self.insert_rows()

        response = Band.filter(popularity__lt=1000).run_sync()

        self.assertEqual([band.name for band in response], ["CSharps"])

    def test_in(self):
        self.insert_rows()

        response = (
            Band.filter(name__in=["Pythonistas", "CSharps"])
            .order_by(Band.name)
            .run_sync()
        )

        self.assertEqual(
            [band.name for band in response], ["CSharps", "Pythonistas"]
        )

    def test_multiple_lookups(self):
        self.insert_rows()

        response = Band.filter(
            name="Pythonistas", popularity__gte=1000
        ).run_sync()

        self.assertEqual([band.name for band in response], ["Pythonistas"])

    def test_related_field(self):
        self.insert_rows()

        response = Band.filter(manager__name="Guido").run_sync()

        self.assertEqual([band.name for band in response], ["Pythonistas"])

    def test_related_field_in(self):
        self.insert_rows()

        response = (
            Band.filter(manager__name__in=["Guido", "Graydon"])
            .order_by(Band.name)
            .run_sync()
        )

        self.assertEqual(
            [band.name for band in response], ["Pythonistas", "Rustaceans"]
        )

    def test_chains_with_where(self):
        self.insert_rows()

        response = (
            Band.filter(popularity__gte=1000)
            .where(Band.name == "Rustaceans")
            .run_sync()
        )

        self.assertEqual([band.name for band in response], ["Rustaceans"])


class TestCriteria(DBTestCase):
    def test_or(self):
        self.insert_rows()

        response = (
            Band.filter(
                Band.criteria(name="Pythonistas")
                | Band.criteria(name="CSharps")
            )
            .order_by(Band.name)
            .run_sync()
        )

        self.assertEqual(
            [band.name for band in response], ["CSharps", "Pythonistas"]
        )

    def test_or_combined_with_lookups(self):
        self.insert_rows()

        response = Band.filter(
            Band.criteria(name="Pythonistas") | Band.criteria(name="CSharps"),
            popularity__gte=1000,
        ).run_sync()

        self.assertEqual([band.name for band in response], ["Pythonistas"])

    def test_works_in_where(self):
        self.insert_rows()

        response = (
            Band.objects()
            .where(
                Band.criteria(popularity__gte=2000) | (Band.name == "CSharps")
            )
            .order_by(Band.name)
            .run_sync()
        )

        self.assertEqual(
            [band.name for band in response], ["CSharps", "Rustaceans"]
        )

    def test_multiple_lookups_are_anded(self):
        self.insert_rows()

        response = (
            Band.objects()
            .where(Band.criteria(name="Pythonistas", popularity__gte=2000))
            .run_sync()
        )

        self.assertEqual(response, [])

    def test_no_lookups(self):
        with self.assertRaises(ValueError):
            Band.criteria()


class TestTransforms(TableTest):
    tables = [Event, Ticket]

    def setUp(self):
        """
        The ``year`` column and the year of ``starts`` disagree on purpose, so
        a test can tell which of the two a lookup used.
        """
        super().setUp()

        mismatched, other = events = [
            Event(
                name="Mismatched",
                year=1999,
                starts=datetime.datetime(2020, 6, 1, 9),
            ),
            Event(
                name="Other",
                year=2020,
                starts=datetime.datetime(1999, 6, 1, 14),
            ),
        ]
        Event.insert(*events).run_sync()

        Ticket.insert(Ticket(event=mismatched), Ticket(event=other)).run_sync()

    def test_transform(self):
        response = Event.filter(starts__year=2020).run_sync()

        self.assertEqual([event.name for event in response], ["Mismatched"])

    def test_transform_with_operator(self):
        response = Event.filter(starts__year__gte=2020).run_sync()

        self.assertEqual([event.name for event in response], ["Mismatched"])

    def test_transform_with_in(self):
        """
        ``Column.is_in`` expands the values, but ``QueryString.is_in`` binds
        the whole list as one parameter - which isn't valid SQL.
        """
        response = (
            Event.filter(starts__year__in=[2020, 1999])
            .order_by(Event.name)
            .run_sync()
        )

        self.assertEqual(
            [event.name for event in response], ["Mismatched", "Other"]
        )

    def test_transform_with_empty_in(self):
        with self.assertRaises(ValueError):
            Event.filter(starts__year__in=[])

    def test_transform_with_sub_select(self):
        """
        ``Other.year`` is 2020, and ``Mismatched.starts`` is the row in 2020.
        """
        response = Event.filter(
            starts__year__in=Event.select(Event.year).where(
                Event.name == "Other"
            )
        ).run_sync()

        self.assertEqual([event.name for event in response], ["Mismatched"])

    def test_related_transform(self):
        response = (
            Ticket.filter(event__starts__year=2020)
            .prefetch(Ticket.event)
            .run_sync()
        )

        self.assertEqual(
            [ticket.event.name for ticket in response], ["Mismatched"]
        )

    def test_related_transform_with_in(self):
        response = (
            Ticket.filter(event__starts__year__in=[2020])
            .prefetch(Ticket.event)
            .run_sync()
        )

        self.assertEqual(
            [ticket.event.name for ticket in response], ["Mismatched"]
        )

    def test_hour_transform(self):
        response = Event.filter(starts__hour=14).run_sync()

        self.assertEqual([event.name for event in response], ["Other"])

    def test_column_wins_over_transform(self):
        """
        ``year`` is both a column and a transform, and the column wins.
        """
        response = Event.filter(year=2020).run_sync()

        self.assertEqual([event.name for event in response], ["Other"])

    def test_related_column_wins_over_transform(self):
        response = (
            Ticket.filter(event__year=2020).prefetch(Ticket.event).run_sync()
        )

        self.assertEqual([ticket.event.name for ticket in response], ["Other"])

    def test_combines_with_or(self):
        """
        Transforms return a ``QueryString``, where ``|`` means ``COALESCE`` -
        so ``criteria`` has to normalise them for ``OR`` to work.
        """
        response = (
            Event.objects()
            .where(
                Event.criteria(starts__year=2020)
                | Event.criteria(starts__year=1999)
            )
            .order_by(Event.name)
            .run_sync()
        )

        self.assertEqual(
            [event.name for event in response], ["Mismatched", "Other"]
        )

    def test_related_transform_in_delete(self):
        """
        ``update``/``delete`` can't join, so a transform on a related column
        has to be rewritten into a sub select.
        """
        Ticket.delete().where(
            Ticket.criteria(event__starts__year=2020)
        ).run_sync()

        remaining = Ticket.objects().prefetch(Ticket.event).run_sync()

        self.assertEqual(
            [ticket.event.name for ticket in remaining], ["Other"]
        )

    def test_transform_in_delete(self):
        Event.delete().where(Event.criteria(starts__year=2020)).run_sync()

        self.assertEqual(
            [event.name for event in Event.objects().run_sync()], ["Other"]
        )


class TestColumnNamedLikeAnOperator(TableTest):
    tables = [Room, Booking]

    def setUp(self):
        super().setUp()

        big, small = rooms = [
            Room(name="Big", lt=100),
            Room(name="Small", lt=1),
        ]
        Room.insert(*rooms).run_sync()
        Booking.insert(Booking(room=big), Booking(room=small)).run_sync()

    def test_column_wins_over_operator(self):
        """
        ``room__lt`` is ``Room.lt``, not ``Booking.room < value``.
        """
        response = Booking.filter(room__lt=1).prefetch(Booking.room).run_sync()

        self.assertEqual(
            [booking.room.name for booking in response], ["Small"]
        )

    def test_operator_still_works(self):
        response = Room.filter(lt__gte=100).run_sync()

        self.assertEqual([room.name for room in response], ["Big"])


class TestLookupParsing(TestCase):
    """
    These never reach the database - the lookup is rejected while the query is
    being built.
    """

    def test_unknown_column(self):
        with self.assertRaises(ValueError):
            Band.filter(genre="jazz")

    def test_unknown_lookup_suffix(self):
        """
        An unrecognised suffix isn't an operator, so it's treated as part of
        the column path - which then fails to resolve.
        """
        with self.assertRaises(ValueError):
            Band.filter(name__nope="Pythonistas")

    def test_column_method_isnt_a_lookup(self):
        """
        The column path is walked with ``getattr``, so ``name__like`` would
        otherwise resolve to ``Varchar.like`` - a method, not a column.
        """
        with self.assertRaises(ValueError):
            Band.filter(name__like="Py%")

    def test_in_with_a_string(self):
        """
        A string is a sequence, so it would otherwise expand into one value
        per character.
        """
        with self.assertRaises(ValueError):
            Band.filter(name__in="Pythonistas")

    def test_in_with_an_empty_sequence(self):
        """
        ``Column.is_in`` only rejects an empty ``list``, but ``IN ()`` isn't
        valid SQL whatever the sequence was.
        """
        for values in ([], (), set(), range(0)):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    Band.filter(name__in=values)

    def test_transform_on_a_non_datetime_column(self):
        """
        Otherwise the transform is applied to whatever the path resolved to,
        and the database is left to reject it.
        """
        with self.assertRaises(ValueError):
            Band.filter(name__year=2020)

        with self.assertRaises(ValueError):
            Band.filter(popularity__month=6)

    def test_lookup_named_like_the_classmethod_argument(self):
        """
        ``cls`` is positional-only, so it can't collide with a lookup.
        """
        with self.assertRaises(ValueError):
            Band.filter(**{"cls": "x"})

        with self.assertRaises(ValueError):
            Band.criteria(**{"cls": "x"})

    def test_call_chain_too_long(self):
        """
        Walking a long path through a self-referencing foreign key raises a
        bare ``Exception``, which still has to come back as a bad lookup.
        """
        lookup = "__".join(["boss"] * 12 + ["name"])

        with self.assertRaises(ValueError):
            Employee.filter(**{lookup: "x"})
