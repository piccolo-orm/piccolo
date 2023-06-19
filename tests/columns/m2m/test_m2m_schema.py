from unittest import TestCase

from piccolo.columns.column_types import (
    ForeignKey,
    LazyTableReference,
    Text,
    Varchar,
)
from piccolo.columns.m2m import M2M
from piccolo.schema import SchemaManager
from piccolo.table import Table
from tests.base import engines_skip

from .base import M2MBase


class Band(Table, schema="schema_1"):
    name = Varchar()
    genres = M2M(LazyTableReference("GenreToBand", module_path=__name__))


class Genre(Table, schema="schema_1"):
    name = Varchar()
    bands = M2M(LazyTableReference("GenreToBand", module_path=__name__))


class GenreToBand(Table, schema="schema_1"):
    band = ForeignKey(Band)
    genre = ForeignKey(Genre)
    reason = Text(help_text="For testing additional columns on join tables.")


@engines_skip("sqlite")
class TestM2MWithSchema(M2MBase, TestCase):
    """
    Make sure that when the tables exist in a non-public schema, that M2M still
    works.
    """

    band = Band
    genre = Genre
    genre_to_band = GenreToBand
    all_tables = [Band, Genre, GenreToBand]

    def tearDown(self):
        SchemaManager().drop_schema(
            schema_name="schema_1", cascade=True
        ).run_sync()
