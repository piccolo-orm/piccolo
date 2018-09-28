from unittest import TestCase

from ..example_project.tables import Pokemon, Trainer


class TestTransaction(TestCase):

    def test_error(self):
        """
        Make sure queries in a transaction aren't committed if a query fails.
        """
        transaction = Pokemon.Meta.db.transaction()
        transaction.add(
            Pokemon.create(),
            Trainer.create(),
            Pokemon.raw('MALFORMED QUERY ... SHOULD ERROR')
        )
        try:
            transaction.run_sync()
        except Exception as error:
            pass
        self.assertTrue(
            not Pokemon.table_exists().run_sync()
        )
        self.assertTrue(
            not Trainer.table_exists().run_sync()
        )

    def test_succeeds(self):
        transaction = Pokemon.Meta.db.transaction()
        transaction.add(
            Pokemon.create(),
            Trainer.create()
        )
        transaction.run_sync()

        self.assertTrue(
            Pokemon.table_exists().run_sync()
        )
        self.assertTrue(
            Trainer.table_exists().run_sync()
        )

        transaction.add(
            Pokemon.drop(),
            Trainer.drop()
        )
        transaction.run_sync()
