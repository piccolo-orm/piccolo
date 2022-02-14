from unittest import TestCase

from piccolo.columns.column_types import Integer
from piccolo.table import Table
from tests.example_apps.music.tables import Manager


class TestIndexes(TestCase):
    def setUp(self):
        Manager.create_table().run_sync()

    def tearDown(self):
        Manager.alter().drop_table().run_sync()

    def test_create_index(self):
        """
        Test single column and multi column indexes.
        """
        for columns in [
            [Manager.name],
            [Manager._meta.primary_key, Manager.name],
        ]:
            Manager.create_index(columns).run_sync()

            index_name = Manager._get_index_name(
                [i._meta.name for i in columns]
            )

            index_names = Manager.indexes().run_sync()
            self.assertIn(index_name, index_names)

            Manager.drop_index(columns).run_sync()
            index_names = Manager.indexes().run_sync()
            self.assertNotIn(index_name, index_names)


class Concert(Table):
    order = Integer()


class TestProblematicColumnName(TestCase):
    def setUp(self):
        Concert.create_table().run_sync()

    def tearDown(self):
        Concert.alter().drop_table().run_sync()

    def test_problematic_name(self):
        """
        Make sure we can add an index to a column with a problematic name
        (which clashes with a SQL keyword).
        """
        columns = [Concert.order]
        Concert.create_index(columns=columns).run_sync()
        index_name = Concert._get_index_name([i._meta.name for i in columns])

        index_names = Concert.indexes().run_sync()
        self.assertIn(index_name, index_names)

        Concert.drop_index(columns).run_sync()
        index_names = Concert.indexes().run_sync()
        self.assertNotIn(index_name, index_names)


class TestIndexName(TestCase):
    def test_index_name(self):
        self.assertEqual(
            Manager._get_index_name(["name", "id"]), "manager_name_id"
        )
