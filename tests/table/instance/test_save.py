from tests.example_project.tables import Band
from tests.base import DBTestCase


class TestSave(DBTestCase):

    def setUp(self):
        Band.create.run_sync()

    def tearDown(self):
        Band.drop.run_sync()

    def test_save_new(self):
        """
        Make sure that saving a new instance works.
        """
        self.insert_rows()

        rubists = Band(
            name='Rubists',
            manager='Maz',
            popularity=300
        )

        query = rubists.save()
        print(query)
        self.assertTrue('INSERT' in query.__str__())

        query.run_sync()

        names = [i['name'] for i in Band.select.columns(Band.name).run_sync()]
        self.assertTrue('Rubists' in names)

        rubists.name = 'Rubists on Rails'
        query = rubists.save()
        print(query)
        self.assertTrue('UPDATE' in query.__str__())

        query.run_sync()
        names = [i['name'] for i in Band.select.columns(Band.name).run_sync()]
        self.assertTrue('Rubists on Rails' in names)
        self.assertTrue('Rubists' not in names)

        # Make sure it has an id too ...
        # and the next query is an UPDATE ...
        # .run(objects=True)
        # .run(as_json=True)
        # Generic('some_table').select('name')
        # -> won't work because where requires things like
        # Band.select().where(Band.id == 1)
        # So doesn't work as a generic query build without first defining
        # the tables.... this is totally fine though.
