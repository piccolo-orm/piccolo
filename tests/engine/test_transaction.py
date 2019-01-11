from unittest import TestCase

from ..example_project.tables import Band, Manager


class TestTransaction(TestCase):

    def test_error(self):
        """
        Make sure queries in a transaction aren't committed if a query fails.
        """
        transaction = Band.Meta.db.transaction()
        transaction.add(
            Manager.create,
            Band.create,
            Band.raw('MALFORMED QUERY ... SHOULD ERROR')
        )
        try:
            transaction.run_sync()
        except Exception:
            pass
        self.assertTrue(
            not Band.table_exists.run_sync()
        )
        self.assertTrue(
            not Manager.table_exists.run_sync()
        )

    def test_succeeds(self):
        transaction = Band.Meta.db.transaction()
        transaction.add(
            Manager.create,
            Band.create
        )
        transaction.run_sync()

        self.assertTrue(
            Band.table_exists.run_sync()
        )
        self.assertTrue(
            Manager.table_exists.run_sync()
        )

        transaction.add(
            Band.drop,
            Manager.drop
        )
        transaction.run_sync()
