from piccolo.query.methods.delete import DeletionError
from tests.base import DBTestCase
from tests.example_apps.music.tables import Band


class TestDelete(DBTestCase):
    def test_delete(self):
        self.insert_rows()

        Band.delete().where(Band.name == "CSharps").run_sync()

        response = Band.count().where(Band.name == "CSharps").run_sync()

        self.assertEqual(response, 0)

    def test_validation(self):
        """
        Make sure you can't delete all the data without forcing it.
        """
        with self.assertRaises(DeletionError):
            Band.delete().run_sync()

        Band.delete(force=True).run_sync()
