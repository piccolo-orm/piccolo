from ..base import DBTestCase
from ..example_project.tables import Band


class TestUpdate(DBTestCase):

    def test_update(self):
        self.insert_rows()

        Band.update().values({
            Band.name: 'Pythonistas3'
        }).where(
            Band.name == 'Pythonistas'
        ).run_sync()

        response = Band.select().columns(
            Band.name
        ).where(
            Band.name == 'Pythonistas3'
        ).run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'Pythonistas3'}]
        )
