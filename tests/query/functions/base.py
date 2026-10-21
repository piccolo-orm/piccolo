from piccolo.testing.test_case import TableTest
from tests.example_apps.music.tables import Band, Manager


class BandTest(TableTest):
    tables = [Band, Manager]

    def setUp(self) -> None:
        super().setUp()

        manager = Manager({Manager.name: "Guido"})
        manager.save().run_sync()

        band = Band(
            {
                Band.name: "Pythonistas",
                Band.manager: manager,
                Band.popularity: 1000,
            }
        )
        band.save().run_sync()
