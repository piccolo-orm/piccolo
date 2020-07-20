from unittest import TestCase

from ..base import DBTestCase
from ..example_project.tables import Manager


class TestCreateIndex(DBTestCase):
    def test_create_index(self):
        """
        Test single column and multi column indexes
        """
        for columns in [[Manager.name], [Manager.id, Manager.name]]:

            index_name = Manager._get_index_name(
                [i._meta.name for i in columns]
            )

            if Manager._meta.db.engine_type == "postgres":
                query = Manager.raw(
                    "SELECT * FROM pg_indexes WHERE indexname = {}", index_name
                )
            else:
                query = Manager.raw(f"PRAGMA index_list(manager)")

            Manager.create_index(columns).run_sync()
            response = query.run_sync()
            self.assertEqual(len(response), 1)

            Manager.drop_index(columns).run_sync()
            response = query.run_sync()
            self.assertEqual(len(response), 0)


class TestIndexName(TestCase):
    def test_index_name(self):
        self.assertEqual(
            Manager._get_index_name(["name", "id"]), "manager_name_id"
        )
