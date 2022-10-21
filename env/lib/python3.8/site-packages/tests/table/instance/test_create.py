from unittest import TestCase

from tests.example_apps.music.tables import Manager


class TestCreate(TestCase):
    def setUp(self):
        Manager.create_table().run_sync()

    def tearDown(self):
        Manager.alter().drop_table().run_sync()

    def test_create_new(self):
        """
        Make sure that creating a new instance works.
        """
        Manager.objects().create(name="Maz").run_sync()

        names = [i["name"] for i in Manager.select(Manager.name).run_sync()]
        self.assertTrue("Maz" in names)
