from piccolo.testing.test_case import AsyncTableTest
from tests.example_apps.music.tables import Band, Manager


class TestUpdateSelf(AsyncTableTest):

    tables = [Band, Manager]

    async def test_update_self(self):
        band = Band({Band.name: "Pythonistas", Band.popularity: 1000})

        # Make sure we get a ValueError if it's not in the database yet.
        with self.assertRaises(ValueError):
            await band.update_self({Band.popularity: Band.popularity + 1})

        # Save it, so it's in the database
        await band.save()

        # Make sure we can successfully update the object
        await band.update_self({Band.popularity: Band.popularity + 1})

        # Make sure the value was updated on the object
        assert band.popularity == 1001

        # Make sure the value was updated in the database
        await band.refresh()
        assert band.popularity == 1001
