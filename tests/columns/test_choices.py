import enum
from unittest import TestCase

from piccolo.columns.column_types import Array, Varchar
from piccolo.table import Table
from tests.base import engines_only
from tests.example_apps.music.tables import Shirt


class TestChoices(TestCase):
    def setUp(self):
        Shirt.create_table().run_sync()

    def tearDown(self):
        Shirt.alter().drop_table().run_sync()

    def _insert_shirts(self):
        Shirt.insert(
            Shirt(size=Shirt.Size.small),
            Shirt(size=Shirt.Size.medium),
            Shirt(size=Shirt.Size.large),
        ).run_sync()

    def test_save(self):
        """
        Make sure saving works, when setting a value as an Enum.
        """
        shirt = Shirt(size=Shirt.Size.large)
        shirt.save().run_sync()

    def test_default(self):
        """
        Make sure the default works correctly, when the default is an Enum.
        """
        Shirt().save().run_sync()
        shirt = Shirt.objects().first().run_sync()
        self.assertEqual(shirt.size, "l")

    def test_update(self):
        """
        Make sure rows can be updated using Enums.
        """
        self._insert_shirts()
        Shirt.update({Shirt.size: Shirt.Size.large}).where(
            Shirt.size == Shirt.Size.small
        ).run_sync()
        shirts = (
            Shirt.select(Shirt.size)
            .output(as_list=True)
            .order_by(Shirt._meta.primary_key)
            .run_sync()
        )
        self.assertEqual(shirts, ["l", "m", "l"])

    def test_select_where(self):
        """
        Make sure Enums can be used in the where clause of select queries.
        """
        self._insert_shirts()
        shirts = (
            Shirt.select(Shirt.size)
            .where(Shirt.size == Shirt.Size.small)
            .run_sync()
        )
        self.assertEqual(shirts, [{"size": "s"}])

    def test_objects_where(self):
        """
        Make sure Enums can be used in the where clause of objects queries.
        """
        self._insert_shirts()
        shirts = (
            Shirt.objects().where(Shirt.size == Shirt.Size.small).run_sync()
        )
        self.assertEqual(len(shirts), 1)
        self.assertEqual(shirts[0].size, "s")


class Ticket(Table):
    class Extras(str, enum.Enum):
        drink = "drink"
        snack = "snack"
        program = "program"

    extras = Array(Varchar(), choices=Extras)


@engines_only("postgres", "sqlite")
class TestArrayChoices(TestCase):
    """
    🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg
    """  # noqa: E501

    def setUp(self):
        Ticket.create_table().run_sync()

    def tearDown(self):
        Ticket.alter().drop_table().run_sync()

    def test_string(self):
        """
        Make sure strings can be passed in as choices.
        """
        ticket = Ticket(extras=["drink", "snack", "program"])
        ticket.save().run_sync()

        self.assertListEqual(
            Ticket.select(Ticket.extras).run_sync(),
            [{"extras": ["drink", "snack", "program"]}],
        )

    def test_enum(self):
        """
        Make sure enums can be passed in as choices.
        """
        ticket = Ticket(
            extras=[
                Ticket.Extras.drink,
                Ticket.Extras.snack,
                Ticket.Extras.program,
            ]
        )
        ticket.save().run_sync()

        self.assertListEqual(
            Ticket.select(Ticket.extras).run_sync(),
            [{"extras": ["drink", "snack", "program"]}],
        )

    def test_invalid_choices(self):
        """
        Make sure an invalid choices Enum is rejected.
        """
        with self.assertRaises(ValueError) as manager:

            class Ticket(Table):
                # This will be rejected, because the values are ints, and the
                # Array's base_column is Varchar.
                class Extras(int, enum.Enum):
                    drink = 1
                    snack = 2
                    program = 3

                extras = Array(Varchar(), choices=Extras)

        self.assertEqual(
            manager.exception.__str__(), "drink doesn't have the correct type"
        )
