import typing as t

from piccolo.testing.test_case import AsyncTableTest
from tests.example_apps.music.tables import Band, Concert, Manager, Venue


class TestGetRelated(AsyncTableTest):
    tables = [Manager, Band, Concert, Venue]

    async def asyncSetUp(self):
        await super().asyncSetUp()

        # Setup two pairs of manager/band, so we can make sure the correct
        # objects are returned.

        self.manager = Manager(name="Guido")
        await self.manager.save()

        self.band = Band(
            name="Pythonistas", manager=self.manager.id, popularity=100
        )
        await self.band.save()

        self.manager_2 = Manager(name="Graydon")
        await self.manager_2.save()

        self.band_2 = Band(
            name="Rustaceans", manager=self.manager_2.id, popularity=100
        )
        await self.band_2.save()

    async def test_foreign_key(self) -> None:
        """
        Make sure you can get a related object from another object instance.
        """
        manager = await self.band.get_related(Band.manager)
        assert manager is not None
        self.assertTrue(manager.id == self.manager.id)

        manager_2 = await self.band_2.get_related(Band.manager)
        assert manager_2 is not None
        self.assertTrue(manager_2.id == self.manager_2.id)

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
        self.assertTrue(manager.id == self.manager.id)

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
        concert = Concert(band_1=self.band, band_2=self.band_2)
        await concert.save()

        manager = await concert.get_related(Concert.band_1._.manager)
        assert manager is not None
        self.assertTrue(manager.id == self.manager.id)

        manager_2 = await concert.get_related(Concert.band_2._.manager)
        assert manager_2 is not None
        self.assertTrue(manager_2.id == self.manager_2.id)

    async def test_no_match(self):
        """
        If not related object exists, make sure ``None`` is returned.
        """
        concert = Concert(band_1=self.band, band_2=None)
        await concert.save()

        manager_2 = await concert.get_related(Concert.band_2._.manager)
        assert manager_2 is None

    async def test_not_in_db(self):
        """
        If the object we're calling ``get_related`` on doesn't exist in the
        database, then make sure an error is raised.
        """
        concert = Concert(band_1=self.band, band_2=self.band_2)

        with self.assertRaises(ValueError):
            await concert.get_related(Concert.band_1._.manager)
