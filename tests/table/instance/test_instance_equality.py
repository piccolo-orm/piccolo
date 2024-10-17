from piccolo.testing.test_case import AsyncTableTest
from tests.example_apps.music.tables import Band, Manager


class TestInstanceEquality(AsyncTableTest):
    tables = [Manager, Band]

    async def asyncSetUp(self):
        await super().asyncSetUp()

        self.manager = Manager(name="Guido")
        await self.manager.save()

        self.band = Band(
            name="Pythonistas", manager=self.manager.id, popularity=100
        )
        await self.band.save()

    async def test_instance_equality(self) -> None:
        """
        Make sure for instance equailty.
        """
        band_pk = await self.band.objects().first()
        band = await self.band.objects(Band.manager).get(
            (Band._meta.primary_key == band_pk.id)
        )
        manager_pk = await self.manager.objects().first()
        manager = await self.manager.objects().get(
            Manager._meta.primary_key == manager_pk.id
        )
        self.assertTrue(band.manager == manager)
