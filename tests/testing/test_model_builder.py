import asyncio
import unittest

from piccolo.testing.model_builder import ModelBuilder
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


class TestModelBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):

        for table_class in (
            Manager,
            Band,
            Poster,
            RecordingStudio,
            Shirt,
            Venue,
            Concert,
            Ticket,
        ):
            table_class.create_table().run_sync()

    @classmethod
    def tearDownClass(cls) -> None:
        for table_class in (
            Ticket,
            Concert,
            Venue,
            Shirt,
            RecordingStudio,
            Poster,
            Band,
            Manager,
        ):
            table_class.alter().drop_table().run_sync()

    def test_model_builder_async(self):
        async def build_model(model):
            return await ModelBuilder.build(model)

        asyncio.run(build_model(Manager))
        asyncio.run(build_model(Ticket))
        asyncio.run(build_model(Poster))
        asyncio.run(build_model(RecordingStudio))

    def test_model_builder_sync(self):
        ModelBuilder.build_sync(Manager)
        ModelBuilder.build_sync(Ticket)
        ModelBuilder.build_sync(Poster)
        ModelBuilder.build_sync(RecordingStudio)

    def test_model_builder_with_choices(self):
        shirt = ModelBuilder.build_sync(Shirt)
        queried_shirt = (
            Shirt.objects().where(Shirt.id == shirt.id).first().run_sync()
        )

        self.assertIn(
            queried_shirt.size,
            ["s", "l", "m"],
        )

    def test_model_builder_with_foreign_key(self):
        ModelBuilder.build_sync(Band)

    def test_model_builder_with_invalid_column(self):
        with self.assertRaises(ValueError):
            ModelBuilder.build_sync(Band, defaults={"X": 1})

    def test_model_builder_with_minimal(self):
        band = ModelBuilder.build_sync(Band, minimal=True)

        self.assertEqual(
            Band.exists().where(Band.id == band.id).run_sync(),
            True,
        )

    def test_model_builder_with_no_persist(self):
        band = ModelBuilder.build_sync(Band, persist=False)

        self.assertEqual(
            Band.exists().where(Band.id == band.id).run_sync(),
            False,
        )

    def test_model_builder_with_valid_column(self):
        manager = ModelBuilder.build_sync(
            Manager, defaults={Manager.name: "Guido"}
        )

        queried_manager = (
            Manager.objects()
            .where(Manager.id == manager.id)
            .first()
            .run_sync()
        )

        self.assertEqual(queried_manager.name, "Guido")

    def test_model_builder_with_valid_column_string(self):
        manager = ModelBuilder.build_sync(Manager, defaults={"name": "Guido"})

        queried_manager = (
            Manager.objects()
            .where(Manager.id == manager.id)
            .first()
            .run_sync()
        )

        self.assertEqual(queried_manager.name, "Guido")

    def test_model_builder_with_valid_foreign_key(self):
        manager = ModelBuilder.build_sync(Manager)

        band = ModelBuilder.build_sync(Band, defaults={Band.manager: manager})

        self.assertEqual(manager._meta.primary_key, band.manager)

    def test_model_builder_with_valid_foreign_key_string(self):
        manager = ModelBuilder.build_sync(Manager)

        band = ModelBuilder.build_sync(Band, defaults={"manager": manager})

        self.assertEqual(manager._meta.primary_key, band.manager)
