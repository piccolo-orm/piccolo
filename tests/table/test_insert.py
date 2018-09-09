from ..base import DBTestCase
from ..example_project.tables import Pokemon


class TestInsert(DBTestCase):

    def test_insert(self):
        self.insert_rows()

        response = Pokemon.insert().add(
            Pokemon()
        ).run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'kakuna'}]
        )
