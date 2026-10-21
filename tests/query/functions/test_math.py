import decimal

from piccolo.columns import Numeric
from piccolo.query.functions.math import Abs, Ceil, Floor, Round
from piccolo.table import Table
from piccolo.testing.test_case import TableTest


class Ticket(Table):
    price = Numeric(digits=(5, 2))


class TestMath(TableTest):

    tables = [Ticket]

    def setUp(self):
        super().setUp()
        self.ticket = Ticket({Ticket.price: decimal.Decimal("36.50")})
        self.ticket.save().run_sync()

    def test_floor(self):
        response = Ticket.select(Floor(Ticket.price, alias="price")).run_sync()
        self.assertListEqual(response, [{"price": decimal.Decimal("36.00")}])

    def test_ceil(self):
        response = Ticket.select(Ceil(Ticket.price, alias="price")).run_sync()
        self.assertListEqual(response, [{"price": decimal.Decimal("37.00")}])

    def test_abs(self):
        self.ticket.price = decimal.Decimal("-1.50")
        self.ticket.save().run_sync()
        response = Ticket.select(Abs(Ticket.price, alias="price")).run_sync()
        self.assertListEqual(response, [{"price": decimal.Decimal("1.50")}])

    def test_round(self):
        response = Ticket.select(Round(Ticket.price, alias="price")).run_sync()
        self.assertListEqual(response, [{"price": decimal.Decimal("37.00")}])
