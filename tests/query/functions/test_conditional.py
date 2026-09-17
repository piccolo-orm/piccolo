from unittest import TestCase

from piccolo.columns import Integer, Text, Varchar
from piccolo.query.functions.conditional import Case, Coalesce, NullIf, When
from piccolo.query.functions.string import Upper
from piccolo.table import Table
from piccolo.testing.test_case import AsyncTableTest


class Band(Table):
    popularity = Integer(null=True, default=None)


class TestCoalesce(AsyncTableTest):

    tables = [Band]

    async def asyncSetUp(self):
        await super().asyncSetUp()
        await Band({Band.popularity: None}).save()

    async def test_coalesce(self):
        response = await Band.select(Coalesce(Band.popularity, 10))
        self.assertListEqual(response, [{"popularity": 10}])

    async def test_coalesce_pipe_syntax(self):
        response = await Band.select(Band.popularity | 10)
        self.assertListEqual(response, [{"popularity": 10}])


class Venue(Table):
    name = Varchar()
    address = Text(null=True)


class TestNullIf(AsyncTableTest):

    tables = [Venue]

    async def test_null_if(self):
        await Venue({Venue.name: "Amazing Venue", Venue.address: ""}).save()

        response = await Venue.select(Venue.name, NullIf(Venue.address, ""))

        self.assertListEqual(
            response, [{"name": "Amazing Venue", "address": None}]
        )


class Ticket(Table):
    name = Varchar()
    price = Integer()


class TestCaseFunction(AsyncTableTest):

    tables = [Ticket]

    async def asyncSetUp(self):
        await super().asyncSetUp()

        await Ticket.insert(
            Ticket({Ticket.name: "Standing", Ticket.price: 10}),
            Ticket({Ticket.name: "Seated", Ticket.price: 50}),
            Ticket({Ticket.name: "VIP", Ticket.price: 100}),
        )

    async def test_string_values(self):
        response = await Ticket.select(
            Ticket.name,
            Case(
                When(Ticket.price >= 100, then="expensive"),
                When(Ticket.price >= 50, then="mid range"),
                default="cheap",
                alias="price_band",
            ),
        ).order_by(Ticket.price)

        self.assertListEqual(
            response,
            [
                {"name": "Standing", "price_band": "cheap"},
                {"name": "Seated", "price_band": "mid range"},
                {"name": "VIP", "price_band": "expensive"},
            ],
        )

    async def test_integer_values(self):
        """
        Make sure integers work - Postgres can't infer the type of a bare
        query parameter inside a ``CASE`` statement.
        """
        response = await Ticket.select(
            Ticket.name,
            Case(
                When(Ticket.price >= 50, then=1),
                default=0,
                alias="is_pricey",
            ),
        ).order_by(Ticket.price)

        self.assertListEqual(
            response,
            [
                {"name": "Standing", "is_pricey": 0},
                {"name": "Seated", "is_pricey": 1},
                {"name": "VIP", "is_pricey": 1},
            ],
        )

    async def test_no_default(self):
        """
        If no ``default`` is given, then null should be returned.
        """
        response = await Ticket.select(
            Ticket.name,
            Case(
                When(Ticket.price >= 100, then="expensive"),
                alias="price_band",
            ),
        ).order_by(Ticket.price)

        self.assertListEqual(
            response,
            [
                {"name": "Standing", "price_band": None},
                {"name": "Seated", "price_band": None},
                {"name": "VIP", "price_band": "expensive"},
            ],
        )

    async def test_combined_condition(self):
        """
        Make sure ``and`` / ``or`` conditions work.
        """
        response = await Ticket.select(
            Ticket.name,
            Case(
                When(
                    (Ticket.price >= 50) & (Ticket.name == "Seated"),
                    then=True,
                ),
                default=False,
                alias="matched",
            ),
        ).order_by(Ticket.price)

        self.assertListEqual(
            response,
            [
                {"name": "Standing", "matched": False},
                {"name": "Seated", "matched": True},
                {"name": "VIP", "matched": False},
            ],
        )

    async def test_column_value(self):
        """
        Make sure a column can be returned by a branch.
        """
        response = await Ticket.select(
            Ticket.name,
            Case(
                When(Ticket.price >= 50, then=Ticket.price),
                default=0,
                alias="premium_price",
            ),
        ).order_by(Ticket.price)

        self.assertListEqual(
            response,
            [
                {"name": "Standing", "premium_price": 0},
                {"name": "Seated", "premium_price": 50},
                {"name": "VIP", "premium_price": 100},
            ],
        )

    async def test_nested_function(self):
        """
        Make sure other functions can be used inside a ``Case``.
        """
        response = await Ticket.select(
            Case(
                When(Ticket.price >= 100, then=Upper(Ticket.name)),
                default=Ticket.name,
                alias="label",
            ),
        ).order_by(Ticket.price)

        self.assertListEqual(
            response,
            [
                {"label": "Standing"},
                {"label": "Seated"},
                {"label": "VIP"},
            ],
        )

    async def test_where_clause(self):
        """
        Make sure a ``Case`` can be used in a where clause.
        """
        response = (
            await Ticket.select(Ticket.name)
            .where(
                Case(
                    When(Ticket.price >= 50, then=1),
                    default=0,
                )
                == 1
            )
            .order_by(Ticket.price)
        )

        self.assertListEqual(
            response,
            [{"name": "Seated"}, {"name": "VIP"}],
        )

    async def test_order_by(self):
        """
        Make sure a ``Case`` can be used to sort the results.
        """
        response = await Ticket.select(Ticket.name).order_by(
            Case(
                When(Ticket.name == "Seated", then=1),
                default=2,
            ),
            Ticket.name,
        )

        self.assertListEqual(
            response,
            [{"name": "Seated"}, {"name": "Standing"}, {"name": "VIP"}],
        )

    async def test_default_alias(self):
        """
        If no alias is given, then ``case`` should be used.
        """
        response = await Ticket.select(
            Case(When(Ticket.price >= 100, then="expensive"))
        ).order_by(Ticket.price)

        self.assertListEqual(
            response,
            [
                {"case": None},
                {"case": None},
                {"case": "expensive"},
            ],
        )

    async def test_query_string_condition(self):
        """
        A condition can be a ``QueryString`` as well as a where clause - a
        function wrapping a column returns one, and ``When`` passes it
        straight through.
        """
        response = await Ticket.select(
            Ticket.name,
            Case(
                When(Upper(Ticket.name).like("SEAT%"), then=1),
                default=0,
                alias="seated",
            ),
        ).order_by(Ticket.name)

        self.assertListEqual(
            response,
            [
                {"name": "Seated", "seated": 1},
                {"name": "Standing", "seated": 0},
                {"name": "VIP", "seated": 0},
            ],
        )


class TestCaseValidation(TestCase):

    def test_no_whens(self):
        with self.assertRaises(ValueError):
            Case(default=1)

    def test_invalid_when(self):
        with self.assertRaises(ValueError):
            Case("not a when")  # type: ignore

    def test_invalid_condition(self):
        with self.assertRaises(ValueError):
            When("not a condition", then=1)  # type: ignore
