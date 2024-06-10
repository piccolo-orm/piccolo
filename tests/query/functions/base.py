import typing as t
from unittest import TestCase

from piccolo.table import Table, create_db_tables_sync, drop_db_tables_sync
from tests.example_apps.music.tables import Band, Manager


class FunctionTest(TestCase):
    tables: t.List[t.Type[Table]]

    def setUp(self) -> None:
        create_db_tables_sync(*self.tables)

    def tearDown(self) -> None:
        drop_db_tables_sync(*self.tables)


class BandTest(FunctionTest):
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
