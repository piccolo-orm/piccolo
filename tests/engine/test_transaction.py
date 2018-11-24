from unittest import TestCase

from ..example_project.tables import Band, Trainer


class TestTransaction(TestCase):

    def test_error(self):
        """
        Make sure queries in a transaction aren't committed if a query fails.
        """
        transaction = Band.Meta.db.transaction()
        transaction.add(
            Band.create(),
            Trainer.create(),
            Band.raw('MALFORMED QUERY ... SHOULD ERROR')
        )
        try:
            transaction.run_sync()
        except Exception as error:
            pass
        self.assertTrue(
            not Band.table_exists().run_sync()
        )
        self.assertTrue(
            not Trainer.table_exists().run_sync()
        )

    def test_succeeds(self):
        transaction = Band.Meta.db.transaction()
        transaction.add(
            Band.create(),
            Trainer.create()
        )
        transaction.run_sync()

        self.assertTrue(
            Band.table_exists().run_sync()
        )
        self.assertTrue(
            Trainer.table_exists().run_sync()
        )

        transaction.add(
            Band.drop(),
            Trainer.drop()
        )
        transaction.run_sync()
