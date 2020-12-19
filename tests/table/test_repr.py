from ..base import DBTestCase
from ..example_app.tables import Manager


class TestTableRepr(DBTestCase):
    def test_repr(self):
        self.assertEqual(Manager().__repr__(), "<Manager: None>")

        self.insert_row()
        manager = Manager.objects().first().run_sync()
        self.assertEqual(manager.__repr__(), f"<Manager: {manager.id}>")
