from ..base import DBTestCase
from ..example_project.tables import Band


class TestUpdate(DBTestCase):

    def test_update(self):
        self.insert_rows()

        Band.update(
            name='kakuna'
        ).where(
            Band.name == 'weedle'
        ).run_sync()

        response = Band.select(
            'name'
        ).where(
            Band.name == 'kakuna'
        ).run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'kakuna'}]
        )
