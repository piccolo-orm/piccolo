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
    genres = M2M(
        LazyTableReference("GenreToBand", module_path="tests.columns.test_m2m")
    )


class Genre(Table):
    name = Varchar()


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

    def test_m2m(self):
        response = Band.select(Band.name, Band.genres(Genre.name)).run_sync()
        self.assertEqual(
            response,
            [
                {"name": "Pythonistas", "genres": ["Rock", "Folk"]},
                {"name": "Rustaceans", "genres": ["Folk"]},
                {"name": "C-Sharps", "genres": ["Rock", "Classical"]},
            ],
        )
