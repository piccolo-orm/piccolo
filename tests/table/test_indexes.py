from unittest import TestCase

from ..base import DBTestCase
from ..example_app.tables import Manager


class TestIndexes(DBTestCase):
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
            self.assertTrue(index_name in index_names)

            Manager.drop_index(columns).run_sync()
            index_names = Manager.indexes().run_sync()
            self.assertTrue(index_name not in index_names)


class TestIndexName(TestCase):
    def test_index_name(self):
        self.assertEqual(
            Manager._get_index_name(["name", "id"]), "manager_name_id"
        )
