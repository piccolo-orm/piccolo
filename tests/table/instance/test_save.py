from unittest import TestCase

from tests.example_project.tables import Manager


class TestSave(TestCase):

    def setUp(self):
        Manager.create.run_sync()

    def tearDown(self):
        Manager.drop.run_sync()

    def test_save_new(self):
        """
        Make sure that saving a new instance works.
        """
        manager = Manager(
            name='Maz',
        )

        query = manager.save
        print(query)
        self.assertTrue('INSERT' in query.__str__())

        query.run_sync()

        names = [
            i['name'] for i in Manager.select.columns(Manager.name).run_sync()
        ]
        self.assertTrue('Maz' in names)

        manager.name = 'Maz2'
        query = manager.save
        print(query)
        self.assertTrue('UPDATE' in query.__str__())

        query.run_sync()
        names = [
            i['name'] for i in Manager.select.columns(Manager.name).run_sync()
        ]
        self.assertTrue('Maz2' in names)
        self.assertTrue('Maz' not in names)

        # Make sure it has an id too ...
        # and the next query is an UPDATE ...
        # .run(objects=True)
        # .run(as_json=True)
        # Generic('some_table').select('name')
        # -> won't work because where requires things like
        # Band.select().where(Band.id == 1)
        # So doesn't work as a generic query build without first defining
        # the tables.... this is totally fine though.
