from unittest import TestCase

from tests.example_project.tables import Manager, Band


TABLES = [Manager, Band]


class TestGetRelated(TestCase):

    def setUp(self):
        for table in TABLES:
            table.create.run_sync()

    def tearDown(self):
        for table in reversed(TABLES):
            table.drop.run_sync()

    def test_get_related(self):
        """
        Make sure you can get a related object from another object instance.
        """
        manager = Manager(
            name="Guido"
        )
        manager.save.run_sync()

        band = Band(
            name='Pythonistas',
            manager=manager.id,
            popularity=100
        )
        band.save.run_sync()

        _manager = band.get_related('manager').run_sync()

        self.assertTrue(
            _manager.name == 'Guido'
        )
