from unittest import TestCase

from ..example_project.tables import Band, Manager
from ..base import postgres_only


@postgres_only
class TestTransaction(TestCase):
    def test_error(self):
        """
        Make sure queries in a transaction aren't committed if a query fails.
        """
        transaction = Band._meta.db.transaction()
        transaction.add(
            Manager.create_table(),
            Band.create_table(),
            Band.raw("MALFORMED QUERY ... SHOULD ERROR"),
        )
        try:
            transaction.run_sync()
        except Exception:
            pass
        self.assertTrue(not Band.table_exists().run_sync())
        self.assertTrue(not Manager.table_exists().run_sync())

    def test_succeeds(self):
        transaction = Band._meta.db.transaction()
        transaction.add(Manager.create_table(), Band.create_table())
        transaction.run_sync()

        self.assertTrue(Band.table_exists().run_sync())
        self.assertTrue(Manager.table_exists().run_sync())

        transaction.add(Band.alter().drop_table(), Manager.alter().drop_table())
        transaction.run_sync()
