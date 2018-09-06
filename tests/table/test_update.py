from ..base import DBTestCase
from ..example_project.tables import Pokemon


class TestUpdate(DBTestCase):

    def test_update(self):
        self.insert_rows()

        Pokemon.update(
            name='kakuna'
        ).where(
            Pokemon.name == 'weedle'
        ).run_sync()

        response = Pokemon.select(
            'name'
        ).where(
            Pokemon.name == 'kakuna'
        ).run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'kakuna'}]
        )
