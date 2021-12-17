from unittest import TestCase

from piccolo.columns.column_types import (
    ForeignKey,
    LazyTableReference,
    Varchar,
)
from piccolo.columns.m2m import M2M
from piccolo.table import Table, create_tables, drop_tables
from tests.base import postgres_only


class Band(Table):
    name = Varchar()
    genres = M2M(LazyTableReference("GenreToBand", module_path=__name__))


class Genre(Table):
    name = Varchar()
    bands = M2M(LazyTableReference("GenreToBand", module_path=__name__))


class GenreToBand(Table):
    band = ForeignKey(Band)
    genre = ForeignKey(Genre)


TABLES = [Band, Genre, GenreToBand]


@postgres_only
class TestM2M(TestCase):
    def setUp(self):
        create_tables(*TABLES, if_not_exists=True)

        Band.insert(
            Band(name="Pythonistas"),
            Band(name="Rustaceans"),
            Band(name="C-Sharps"),
        ).run_sync()

        Genre.insert(
            Genre(name="Rock"),
            Genre(name="Folk"),
            Genre(name="Classical"),
        ).run_sync()

        GenreToBand.insert(
            GenreToBand(genre=1, band=1),
            GenreToBand(genre=2, band=1),
            GenreToBand(genre=2, band=2),
            GenreToBand(genre=1, band=3),
            GenreToBand(genre=3, band=3),
        ).run_sync()

    def tearDown(self):
        drop_tables(*TABLES)

    def test_select(self):
        response = Band.select(Band.name, Band.genres(Genre.name)).run_sync()
        self.assertEqual(
            response,
            [
                {"name": "Pythonistas", "genres": ["Rock", "Folk"]},
                {"name": "Rustaceans", "genres": ["Folk"]},
                {"name": "C-Sharps", "genres": ["Rock", "Classical"]},
            ],
        )

        # Now try it in reverse.
        response = Genre.select(Genre.name, Genre.bands(Band.name)).run_sync()
        self.assertEqual(
            response,
            [
                {"name": "Rock", "bands": ["Pythonistas", "C-Sharps"]},
                {"name": "Folk", "bands": ["Pythonistas", "Rustaceans"]},
                {"name": "Classical", "bands": ["C-Sharps"]},
            ],
        )

    def test_add_m2m(self):
        """
        Make sure we can add items to the joining table.
        """
        band: Band = Band.objects().get(Band.name == "Pythonistas").run_sync()
        band.add_m2m(Genre(name="Punk Rock"), m2m=Band.genres).run_sync()

        self.assertTrue(
            Genre.exists().where(Genre.name == "Punk Rock").run_sync()
        )

        self.assertEqual(
            GenreToBand.count()
            .where(
                GenreToBand.band.name == "Pythonistas",
                GenreToBand.genre.name == "Punk Rock",
            )
            .run_sync(),
            1,
        )

    def test_get_m2m(self):
        """
        Make sure we can get related items via the joining table.
        """
        band: Band = Band.objects().get(Band.name == "Pythonistas").run_sync()

        genres = band.get_m2m(Band.genres).run_sync()

        self.assertTrue(all([isinstance(i, Table) for i in genres]))

        self.assertEqual([i.name for i in genres], ["Rock", "Folk"])
