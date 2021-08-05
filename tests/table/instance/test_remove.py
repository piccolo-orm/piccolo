from unittest import TestCase

from tests.example_app.tables import Manager


class TestRemove(TestCase):
    def setUp(self):
        Manager.create_table().run_sync()

    def tearDown(self):
        Manager.alter().drop_table().run_sync()

    def test_remove(self):
        manager = Manager(name="Maz")
        manager.save().run_sync()
        self.assertTrue(
            "Maz"
            in Manager.select(Manager.name).output(as_list=True).run_sync()
        )

        manager.remove().run_sync()
        self.assertTrue(
            "Maz"
            not in Manager.select(Manager.name).output(as_list=True).run_sync()
        )
