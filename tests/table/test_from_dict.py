from unittest import TestCase

from piccolo.columns import Varchar
from piccolo.table import Table


class BandMember(Table):
    name = Varchar(length=50, index=True)


class TestCreateFromDict(TestCase):
    def setUp(self):
        BandMember.create_table().run_sync()

    def tearDown(self):
        BandMember.alter().drop_table().run_sync()

    def test_create_table_from_dict(self):
        BandMember.from_dict({"name": "John"}).save().run_sync()
        self.assertEqual(
            BandMember.select(BandMember.name).run_sync(), [{"name": "John"}]
        )
        BandMember.from_dict({"name": "Town"}).save().run_sync()
        self.assertEqual(BandMember.count().run_sync(), 2)
        self.assertEqual(
            BandMember.select(BandMember.name).run_sync(),
            [{"name": "John"}, {"name": "Town"}],
        )
