from unittest import TestCase

from tests.example_project.tables import Manager


class TestDelete(TestCase):
    def setUp(self):
        Manager.create_table().run_sync()

    def tearDown(self):
        Manager.alter().drop_table().run_sync()

    def test_delete(self):
        manager = Manager(name="Maz")

        manager.save().run_sync()
        manager.remove().run_sync()

        # how can I implement 'flat=True'
        # Band.select(Band.name).output(as_list=True).run_sync()
        #
        Manager.select(Manager.name).run_sync()
