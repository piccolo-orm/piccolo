import unittest

from piccolo.testing.exceptions import InvalidColumnError
from piccolo.testing.model_builder import ModelBuilder

from ..example_app.tables import (
    Band,
    Manager,
    Poster,
    RecordingStudio,
    Shirt,
    Ticket,
)


class TestModelBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Manager.create_table().run_sync()
        Band.create_table().run_sync()
        Poster.create_table().run_sync()
        RecordingStudio.create_table().run_sync()
        Shirt.create_table().run_sync()
        Ticket.create_table().run_sync()

    def test_model_builder(self):
        ModelBuilder().build(Manager)
        ModelBuilder().build(Ticket)
        ModelBuilder().build(Poster)
        ModelBuilder().build(RecordingStudio)

    def test_model_builder_with_choices(self):
        shirt = ModelBuilder().build(Shirt)
        queried_shirt = (
            Shirt.objects().where(Shirt.id == shirt.id).first().run_sync()
        )

        self.assertIn(
            queried_shirt.size,
            ["s", "l", "m"],
        )

    def test_model_builder_with_foreign_key(self):
        ModelBuilder().build(Band)

    def test_model_builder_with_invalid_column(self):
        with self.assertRaises(InvalidColumnError):
            ModelBuilder().build(Band, x=1)

    def test_model_builder_with_minimal(self):
        band = ModelBuilder(minimal=True).build(Band)

        self.assertEqual(
            Band.exists().where(Band.id == band.id).run_sync(),
            True,
        )

    def test_model_builder_with_no_persist(self):
        band = ModelBuilder(persist=False).build(Band)

        self.assertEqual(
            Band.exists().where(Band.id == band.id).run_sync(),
            False,
        )

    def test_model_builder_with_valid_column(self):
        manager = ModelBuilder().build(Manager, name="Guido")

        queried_manager = (
            Manager.objects()
            .where(Manager.id == manager.id)
            .first()
            .run_sync()
        )

        self.assertEqual(queried_manager.name, "Guido")

    def test_model_builder_with_valid_foreign_key(self):
        manager = ModelBuilder().build(Manager)

        band = ModelBuilder().build(Band, manager=manager)

        self.assertEqual(manager._meta.primary_key, band.manager)
