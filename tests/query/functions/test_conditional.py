from piccolo.columns import Integer, Text, Varchar
from piccolo.query.functions.conditional import Coalesce, NullIf
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
