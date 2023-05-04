from unittest import TestCase

from piccolo.columns import Integer, Varchar
from piccolo.table import Table


class Band(Table):
    name = Varchar(default=None, null=False)
    popularity = Integer()


class TestCreate(TestCase):
    def setUp(self):
        Band.create_table().run_sync()

    def tearDown(self):
        Band.alter().drop_table().run_sync()

    def test_create_new(self):
        """
        Make sure that creating a new instance works.
        """
        Band.objects().create(name="Pythonistas", popularity=1000).run_sync()

        names = [i["name"] for i in Band.select(Band.name).run_sync()]
        self.assertTrue("Pythonistas" in names)

    def test_null_values(self):
        """
        Make sure we test non-null columns:
        https://github.com/piccolo-orm/piccolo/issues/652
        """
        with self.assertRaises(ValueError) as manager:
            Band.objects().create().run_sync()

        self.assertEqual(str(manager.exception), "name wasn't provided")

        # Shouldn't raise an exception
        Band.objects().create(name="Pythonistas").run_sync()
