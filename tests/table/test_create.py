from unittest import TestCase

from piccolo.table import Table
from piccolo.columns import Varchar

from ..example_project.tables import Manager


class TestCreate(TestCase):
    def test_create_table(self):
        Manager.create_table().run_sync()
        self.assertTrue(Manager.table_exists().run_sync())

        Manager.alter().drop_table().run_sync()


class BandMember(Table):
    name = Varchar(length=50, index=True)


class TestCreateWithIndexes(TestCase):
    def setUp(self):
        BandMember.create_table().run_sync()

    def tearDown(self):
        BandMember.alter().drop_table().run_sync()

    def test_create_table_with_indexes(self):
        index_names = BandMember.indexes().run_sync()
        index_name = BandMember._get_index_name(["name"])
        self.assertTrue(index_name in index_names)
