from ..base import DBTestCase, postgres_only
from ..example_project.tables import Manager


@postgres_only
class TestCreateIndex(DBTestCase):
    def test_create_index(self):
        """
        Test single column and multi column indexes
        """
        for columns in [[Manager.name], [Manager.id, Manager.name]]:
            query = Manager.raw(
                "SELECT * FROM pg_indexes WHERE indexname = {}",
                Manager._get_index_name([i._meta.name for i in columns]),
            )

            Manager.create_index(columns).run_sync()
            response = query.run_sync()
            self.assertEqual(len(response), 1)

            Manager.drop_index(columns).run_sync()
            response = query.run_sync()
            self.assertEqual(len(response), 0)

    def test_index_name(self):
        self.assertEqual(
            Manager._get_index_name(["name", "id"]), "manager_name_id"
        )
