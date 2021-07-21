from tests.base import DBTestCase
from tests.example_app.tables import Band


class TestGetRelatedReadable(DBTestCase):
    def test_get_related_readable(self):
        """
        Make sure you can get the `Readable` representation for related object
        from another object instance.
        """
        self.insert_row()

        response = Band.select(
            Band.name, Band._get_related_readable(Band.manager)
        ).run_sync()

        self.assertEqual(
            response, [{"name": "Pythonistas", "manager_readable": "Guido"}]
        )

        # TODO Need to make sure it can go two levels deep ...
        # e.g. Concert._get_related_readable(Concert.band_1.manager)
