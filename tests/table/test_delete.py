from ..base import DBTestCase
from ..example_project.tables import Pokemon


class TestDelete(DBTestCase):

    def test_delete(self):
        self.insert_rows()

        Pokemon.delete().where(
            Pokemon.name == 'weedle'
        ).run_sync()

        response = Pokemon.select().where(
            Pokemon.name == 'weedle'
        ).count().run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'count': 0}]
        )
