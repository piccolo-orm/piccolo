from tests.base import DBTestCase
from tests.example_apps.music.tables import Shirt


class TestChoices(DBTestCase):
    def _insert_shirts(self):
        Shirt.insert(
            Shirt(size=Shirt.Size.small),
            Shirt(size=Shirt.Size.medium),
            Shirt(size=Shirt.Size.large),
        ).run_sync()

    def test_save(self):
        """
        Make sure saving works, when setting a value as an Enum.
        """
        shirt = Shirt(size=Shirt.Size.large)
        shirt.save().run_sync()

    def test_default(self):
        """
        Make sure the default works correctly, when the default is an Enum.
        """
        Shirt().save().run_sync()
        shirt = Shirt.objects().first().run_sync()
        self.assertEqual(shirt.size, "l")

    def test_update(self):
        """
        Make sure rows can be updated using Enums.
        """
        self._insert_shirts()
        Shirt.update({Shirt.size: Shirt.Size.large}).where(
            Shirt.size == Shirt.Size.small
        ).run_sync()
        shirts = (
            Shirt.select(Shirt.size)
            .output(as_list=True)
            .order_by(Shirt._meta.primary_key)
            .run_sync()
        )
        self.assertEqual(shirts, ["l", "m", "l"])

    def test_select_where(self):
        """
        Make sure Enums can be used in the where clause of select queries.
        """
        self._insert_shirts()
        shirts = (
            Shirt.select(Shirt.size)
            .where(Shirt.size == Shirt.Size.small)
            .run_sync()
        )
        self.assertEqual(shirts, [{"size": "s"}])

    def test_objects_where(self):
        """
        Make sure Enums can be used in the where clause of objects queries.
        """
        self._insert_shirts()
        shirts = (
            Shirt.objects().where(Shirt.size == Shirt.Size.small).run_sync()
        )
        self.assertEqual(len(shirts), 1)
        self.assertEqual(shirts[0].size, "s")
