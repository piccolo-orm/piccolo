from tests.base import DBTestCase
from tests.example_apps.music.tables import Manager


class TestTableRepr(DBTestCase):
    def test_repr_postgres(self):
        self.assertEqual(
            Manager().__repr__(),
            "<Manager: None>",
        )

        self.insert_row()
        manager = Manager.objects().first().run_sync()
        self.assertEqual(manager.__repr__(), "<Manager: 1>")
