from ..base import DBTestCase, postgres_only
from ..example_project.tables import Manager


@postgres_only
class TestCreateIndex(DBTestCase):
    def test_create_index(self):
        query = Manager.raw(
            "SELECT * FROM pg_indexes WHERE indexname = {}",
            Manager.name._meta.index_name,
        )

        Manager.create_index(Manager.name).run_sync()
        response = query.run_sync()
        self.assertEqual(len(response), 1)

        Manager.drop_index(Manager.name).run_sync()
        response = query.run_sync()
        self.assertEqual(len(response), 0)
