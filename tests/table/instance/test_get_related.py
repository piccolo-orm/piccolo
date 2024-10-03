import typing as t

from piccolo.testing.test_case import AsyncTableTest
from tests.example_apps.music.tables import Band, Concert, Manager, Venue


class TestGetRelated(AsyncTableTest):
    tables = [Manager, Band, Concert, Venue]

    async def asyncSetUp(self):
        await super().asyncSetUp()

        self.manager = Manager(name="Guido")
        await self.manager.save()

        self.band = Band(
            name="Pythonistas", manager=self.manager.id, popularity=100
        )
        await self.band.save()

    async def test_foreign_key(self) -> None:
        """
        Make sure you can get a related object from another object instance.
        """
        manager = await self.band.get_related(Band.manager)
        assert manager is not None
        self.assertTrue(manager.name == "Guido")

    async def test_non_foreign_key(self):
        """
        Make sure that non-ForeignKey raise an exception.
        """
        with self.assertRaises(ValueError):
            self.band.get_related(Band.name)  # type: ignore

    async def test_string(self):
        """
        Make sure it also works using a string representation of a foreign key.
        """
        manager = t.cast(Manager, await self.band.get_related("manager"))
        self.assertTrue(manager.name == "Guido")

    async def test_invalid_string(self):
        """
        Make sure an exception is raised if the foreign key string is invalid.
        """
        with self.assertRaises(ValueError):
            self.band.get_related("abc123")

    async def test_multiple_levels(self):
        """
        Make sure ``get_related`` works multiple levels deep.
        """
        concert = Concert(band_1=self.band)
        await concert.save()

        manager = await concert.get_related(Concert.band_1._.manager)
        assert manager is not None
        self.assertTrue(manager.name == "Guido")

        band_2_manager = await concert.get_related(Concert.band_2._.manager)
        assert band_2_manager is None
