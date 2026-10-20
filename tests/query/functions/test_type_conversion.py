from piccolo.columns import Integer, Text, Varchar
from piccolo.query.functions import Cast, Length
from tests.example_apps.music.tables import Band, Manager

from .base import BandTest


class TestCast(BandTest):
    def test_varchar(self):
        """
        Make sure that casting to ``Varchar`` works.
        """
        response = Band.select(
            Cast(
                Band.popularity,
                as_type=Varchar(),
            )
        ).run_sync()

        self.assertListEqual(
            response,
            [{"popularity": "1000"}],
        )

    def test_text(self):
        """
        Make sure that casting to ``Text`` works.
        """
        response = Band.select(
            Cast(
                Band.popularity,
                as_type=Text(),
            )
        ).run_sync()

        self.assertListEqual(
            response,
            [{"popularity": "1000"}],
        )

    def test_integer(self):
        """
        Make sure that casting to ``Integer`` works.
        """
        Band.update({Band.name: "1111"}, force=True).run_sync()

        response = Band.select(
            Cast(
                Band.name,
                as_type=Integer(),
            )
        ).run_sync()

        self.assertListEqual(
            response,
            [{"name": 1111}],
        )

    def test_join(self):
        """
        Make sure that casting works with joins.
        """
        Manager.update({Manager.name: "1111"}, force=True).run_sync()

        response = Band.select(
            Band.name,
            Cast(
                Band.manager.name,
                as_type=Integer(),
            ),
        ).run_sync()

        self.assertListEqual(
            response,
            [
                {
                    "name": "Pythonistas",
                    "manager.name": 1111,
                }
            ],
        )

    def test_nested_inner(self):
        """
        Make sure ``Cast`` can be passed into other functions.
        """
        Band.update({Band.name: "1111"}, force=True).run_sync()

        response = Band.select(
            Length(
                Cast(
                    Band.popularity,
                    as_type=Varchar(),
                )
            )
        ).run_sync()

        self.assertListEqual(
            response,
            [{"length": 4}],
        )

    def test_nested_outer(self):
        """
        Make sure a querystring can be passed into ``Cast`` (meaning it can be
        nested).
        """
        response = Band.select(
            Cast(
                Length(Band.name),
                as_type=Varchar(),
                alias="length",
            )
        ).run_sync()

        self.assertListEqual(
            response,
            [{"length": str(len("Pythonistas"))}],
        )

    def test_where_clause(self):
        """
        Make sure ``Cast`` works in a where clause.
        """
        response = (
            Band.select(Band.name, Band.popularity)
            .where(Cast(Band.popularity, Varchar()) == "1000")
            .run_sync()
        )

        self.assertListEqual(
            response,
            [{"name": "Pythonistas", "popularity": 1000}],
        )
