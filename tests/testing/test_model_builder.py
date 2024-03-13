import asyncio
import json
import typing as t
import unittest

from piccolo.columns import (
    Array,
    Decimal,
    ForeignKey,
    Integer,
    LazyTableReference,
    Numeric,
    Real,
    Timestamp,
    Timestamptz,
    Varchar,
)
from piccolo.table import Table, create_db_tables_sync, drop_db_tables_sync
from piccolo.testing.model_builder import ModelBuilder
from tests.base import engines_skip
from tests.example_apps.music.tables import (
    Band,
    Concert,
    Manager,
    Poster,
    RecordingStudio,
    Shirt,
    Ticket,
    Venue,
)


class TableWithArrayField(Table):
    strings = Array(Varchar(30))
    integers = Array(Integer())
    floats = Array(Real())


class TableWithDecimal(Table):
    numeric = Numeric()
    numeric_with_digits = Numeric(digits=(4, 2))
    decimal = Decimal()
    decimal_with_digits = Decimal(digits=(4, 2))


class BandWithLazyReference(Table):
    manager: ForeignKey["Manager"] = ForeignKey(
        references=LazyTableReference(
            "Manager", module_path="tests.example_apps.music.tables"
        )
    )


class BandWithRecursiveReference(Table):
    manager: ForeignKey["Manager"] = ForeignKey("self")


TABLES = (
    Manager,
    Band,
    Poster,
    RecordingStudio,
    Shirt,
    Venue,
    Concert,
    Ticket,
    TableWithArrayField,
    TableWithDecimal,
    BandWithLazyReference,
    BandWithRecursiveReference,
)


# Cockroach Bug: Can turn ON when resolved: https://github.com/cockroachdb/cockroach/issues/71908  # noqa: E501
@engines_skip("cockroach")
class TestModelBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_db_tables_sync(*TABLES)

    @classmethod
    def tearDownClass(cls) -> None:
        drop_db_tables_sync(*TABLES)

    def test_async(self):
        async def build_model(table_class: t.Type[Table]):
            return await ModelBuilder.build(table_class)

        for table_class in TABLES:
            asyncio.run(build_model(table_class))

    def test_sync(self):
        for table_class in TABLES:
            ModelBuilder.build_sync(table_class)

    def test_choices(self):
        shirt = ModelBuilder.build_sync(Shirt)
        queried_shirt = (
            Shirt.objects().where(Shirt.id == shirt.id).first().run_sync()
        )
        assert queried_shirt is not None

        self.assertIn(
            queried_shirt.size,
            ["s", "l", "m"],
        )

    def test_datetime(self):
        """
        Make sure that ``ModelBuilder`` generates timezone aware datetime
        objects for ``Timestamptz`` columns, and timezone naive datetime
        objects for ``Timestamp`` columns.
        """

        class Table1(Table):
            starts = Timestamptz()

        class Table2(Table):
            starts = Timestamp()

        model_1 = ModelBuilder.build_sync(Table1, persist=False)
        assert model_1.starts.tzinfo is not None

        model_2 = ModelBuilder.build_sync(Table2, persist=False)
        assert model_2.starts.tzinfo is None

    def test_foreign_key(self):
        model = ModelBuilder.build_sync(Band, persist=True)

        self.assertTrue(
            Manager.exists().where(Manager.id == model.manager).run_sync()
        )

    def test_lazy_foreign_key(self):
        model = ModelBuilder.build_sync(BandWithLazyReference, persist=True)

        self.assertTrue(
            Manager.exists().where(Manager.id == model.manager).run_sync()
        )

    def test_recursive_foreign_key(self):
        """
        Make sure no infinite loops are created with recursive foreign keys.
        """
        model = ModelBuilder.build_sync(
            BandWithRecursiveReference, persist=True
        )
        # It should be set to None, as this foreign key is nullable.
        self.assertIsNone(model.manager)

    def test_invalid_column(self):
        with self.assertRaises(ValueError):
            ModelBuilder.build_sync(Band, defaults={"X": 1})

    def test_minimal(self):
        band = ModelBuilder.build_sync(Band, minimal=True)

        self.assertTrue(Band.exists().where(Band.id == band.id).run_sync())

    def test_persist_false(self):
        band = ModelBuilder.build_sync(Band, persist=False)

        self.assertFalse(Band.exists().where(Band.id == band.id).run_sync())

    def test_valid_column(self):
        manager = ModelBuilder.build_sync(
            Manager, defaults={Manager.name: "Guido"}
        )

        queried_manager = (
            Manager.objects()
            .where(Manager.id == manager.id)
            .first()
            .run_sync()
        )
        assert queried_manager is not None

        self.assertEqual(queried_manager.name, "Guido")

    def test_valid_column_string(self):
        manager = ModelBuilder.build_sync(Manager, defaults={"name": "Guido"})

        queried_manager = (
            Manager.objects()
            .where(Manager.id == manager.id)
            .first()
            .run_sync()
        )
        assert queried_manager is not None

        self.assertEqual(queried_manager.name, "Guido")

    def test_valid_foreign_key(self):
        manager = ModelBuilder.build_sync(Manager)

        band = ModelBuilder.build_sync(Band, defaults={Band.manager: manager})

        self.assertEqual(manager._meta.primary_key, band.manager)

    def test_valid_foreign_key_string(self):
        manager = ModelBuilder.build_sync(Manager)

        band = ModelBuilder.build_sync(Band, defaults={"manager": manager})

        self.assertEqual(manager._meta.primary_key, band.manager)

    def test_json(self):
        """
        Make sure the generated JSON can be parsed.

        This is important, because we might have queries like this::

            >>> await RecordingStudio.select().output(load_json=True)

        """
        studio = ModelBuilder.build_sync(RecordingStudio)
        self.assertIsInstance(json.loads(studio.facilities), dict)
        self.assertIsInstance(json.loads(studio.facilities_b), dict)

        for facilities in (
            RecordingStudio.select(RecordingStudio.facilities)
            .output(load_json=True, as_list=True)
            .run_sync()
        ):
            self.assertIsInstance(facilities, dict)
