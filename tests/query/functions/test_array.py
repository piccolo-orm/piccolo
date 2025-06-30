from piccolo.columns import Array, Integer
from piccolo.query.functions.array import (
    ArrayAppend,
    ArrayCat,
    ArrayPrepend,
    ArrayRemove,
    ArrayReplace,
)
from piccolo.table import Table
from piccolo.testing.test_case import TableTest
from tests.base import engines_only, sqlite_only


class Ticket(Table):
    seat_numbers = Array(base_column=Integer())


class ArrayTest(TableTest):
    tables = [Ticket]

    def setUp(self) -> None:
        super().setUp()
        self.ticket = Ticket(seat_numbers=[34, 35, 36])
        self.ticket.save().run_sync()


@engines_only("postgres", "cockroach")
class TestArrayFunctions(ArrayTest):
    def test_array_append(self):
        ticket_pk = Ticket.select(Ticket.id).first().run_sync()
        # append item to the end of an array
        Ticket.update(
            {Ticket.seat_numbers: ArrayAppend(Ticket.seat_numbers, 37)}
        ).where(Ticket._meta.primary_key == ticket_pk["id"]).run_sync()

        self.assertEqual(
            Ticket.select(Ticket.seat_numbers).run_sync(),
            [{"seat_numbers": [34, 35, 36, 37]}],
        )

    def test_array_cat(self):
        ticket_pk = Ticket.select(Ticket.id).first().run_sync()
        # concatenate two arrays
        Ticket.update(
            {Ticket.seat_numbers: ArrayCat(Ticket.seat_numbers, [37, 38])}
        ).where(Ticket._meta.primary_key == ticket_pk["id"]).run_sync()

        self.assertEqual(
            Ticket.select(Ticket.seat_numbers).run_sync(),
            [{"seat_numbers": [34, 35, 36, 37, 38]}],
        )

    @sqlite_only
    def test_cat_sqlite(self):
        """
        If using SQLite then an exception should be raised currently.
        """
        with self.assertRaises(ValueError) as manager:
            ticket_pk = Ticket.select(Ticket.id).first().run_sync()
            Ticket.update(
                {Ticket.seat_numbers: ArrayCat(Ticket.seat_numbers, [37, 38])}
            ).where(Ticket._meta.primary_key == ticket_pk["id"]).run_sync()

        self.assertEqual(
            str(manager.exception),
            "Only Postgres and Cockroach support array concatenating.",
        )

    def test_array_prepend(self):
        ticket_pk = Ticket.select(Ticket.id).first().run_sync()
        # append item to the beginning of an array
        Ticket.update(
            {Ticket.seat_numbers: ArrayPrepend(33, Ticket.seat_numbers)}
        ).where(Ticket._meta.primary_key == ticket_pk["id"]).run_sync()

        self.assertEqual(
            Ticket.select(Ticket.seat_numbers).run_sync(),
            [{"seat_numbers": [33, 34, 35, 36]}],
        )

    @sqlite_only
    def test_prepend_sqlite(self):
        """
        If using SQLite then an exception should be raised currently.
        """
        with self.assertRaises(ValueError) as manager:
            ticket_pk = Ticket.select(Ticket.id).first().run_sync()
            Ticket.update(
                {Ticket.seat_numbers: ArrayPrepend(33, Ticket.seat_numbers)}
            ).where(Ticket._meta.primary_key == ticket_pk["id"]).run_sync()

        self.assertEqual(
            str(manager.exception),
            "Only Postgres and Cockroach support array prepending.",
        )

    def test_array_replace(self):
        ticket_pk = Ticket.select(Ticket.id).first().run_sync()
        # replace each array item equal to the given value
        # with a new value
        Ticket.update(
            {Ticket.seat_numbers: ArrayReplace(Ticket.seat_numbers, 35, 32)}
        ).where(Ticket._meta.primary_key == ticket_pk["id"]).run_sync()

        self.assertEqual(
            Ticket.select(Ticket.seat_numbers).run_sync(),
            [{"seat_numbers": [34, 32, 36]}],
        )

    @sqlite_only
    def test_replace_sqlite(self):
        """
        If using SQLite then an exception should be raised currently.
        """
        with self.assertRaises(ValueError) as manager:
            ticket_pk = Ticket.select(Ticket.id).first().run_sync()
            Ticket.update(
                {
                    Ticket.seat_numbers: ArrayReplace(
                        Ticket.seat_numbers, 35, 32
                    )
                }
            ).where(Ticket._meta.primary_key == ticket_pk["id"]).run_sync()

        self.assertEqual(
            str(manager.exception),
            "Only Postgres and Cockroach support array substitution.",
        )

    def test_array_remove(self):
        ticket_pk = Ticket.select(Ticket.id).first().run_sync()
        # remove item from an array
        Ticket.update(
            {Ticket.seat_numbers: ArrayRemove(Ticket.seat_numbers, 36)}
        ).where(Ticket._meta.primary_key == ticket_pk["id"]).run_sync()

        self.assertEqual(
            Ticket.select(Ticket.seat_numbers).run_sync(),
            [{"seat_numbers": [34, 35]}],
        )

    @sqlite_only
    def test_remove_sqlite(self):
        """
        If using SQLite then an exception should be raised currently.
        """
        with self.assertRaises(ValueError) as manager:
            ticket_pk = Ticket.select(Ticket.id).first().run_sync()
            Ticket.update(
                {Ticket.seat_numbers: ArrayRemove(Ticket.seat_numbers, 36)}
            ).where(Ticket._meta.primary_key == ticket_pk["id"]).run_sync()

        self.assertEqual(
            str(manager.exception),
            "Only Postgres and Cockroach support array removing.",
        )
