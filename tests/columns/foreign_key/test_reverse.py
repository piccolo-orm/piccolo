from piccolo.columns import ForeignKey, Text, Varchar
from piccolo.table import Table
from piccolo.testing.test_case import TableTest
from tests.base import engines_skip


class Band(Table):
    name = Varchar()


class FanClub(Table):
    address = Text()
    band = ForeignKey(Band, unique=True)


class Treasurer(Table):
    name = Varchar()
    fan_club = ForeignKey(FanClub, unique=True)


@engines_skip("mysql")
class TestReverse(TableTest):
    tables = [Band, FanClub, Treasurer]

    def setUp(self):
        super().setUp()

        band = Band({Band.name: "Pythonistas"})
        band.save().run_sync()

        fan_club = FanClub(
            {FanClub.band: band, FanClub.address: "1 Flying Circus, UK"}
        )
        fan_club.save().run_sync()

        treasurer = Treasurer(
            {Treasurer.fan_club: fan_club, Treasurer.name: "Bob"}
        )
        treasurer.save().run_sync()

    def test_reverse(self):

        response = Band.select(
            Band.name,
            FanClub.band.reverse().address.as_alias("address"),
            Treasurer.fan_club._.band.reverse().name.as_alias(
                "treasurer_name"
            ),
        ).run_sync()
        self.assertListEqual(
            response,
            [
                {
                    "name": "Pythonistas",
                    "address": "1 Flying Circus, UK",
                    "treasurer_name": "Bob",
                }
            ],
        )
