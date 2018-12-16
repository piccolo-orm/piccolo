from ..base import DBTestCase
from ..example_project.tables import Band


class TestDelete(DBTestCase):

    def test_delete(self):
        self.insert_rows()

        Band.delete.where(
            Band.name == 'CSharps'
        ).run_sync()

        response = Band.select.where(
            Band.name == 'CSharps'
        ).count().run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'count': 0}]
        )
