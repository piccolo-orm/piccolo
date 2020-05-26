import decimal
from unittest import TestCase

from piccolo.columns import Integer, Numeric
from piccolo.table import Table

from ..base import DBTestCase, postgres_only
from ..example_project.tables import Band, Manager


class TestRenameColumn(DBTestCase):
    def _test_rename(self, column):
        self.insert_row()

        rename_query = Band.alter().rename_column(column, "rating")
        rename_query.run_sync()

        select_query = Band.raw("SELECT * FROM band")
        response = select_query.run_sync()

        column_names = response[0].keys()
        self.assertTrue(
            ("rating" in column_names) and ("popularity" not in column_names)
        )

    def test_rename_string(self):
        self._test_rename(Band.popularity)

    def test_rename_column(self):
        self._test_rename("popularity")


class TestRenameTable(DBTestCase):
    def test_rename(self):
        Band.alter().rename_table("act").run_sync()
        self.assertEqual(Band.raw("SELECT * FROM act").run_sync(), [])

    def tearDown(self):
        super().tearDown()
        self.run_sync("DROP TABLE IF EXISTS act")


@postgres_only
class TestDropColumn(DBTestCase):
    """
    Unfortunately this only works with Postgres at the moment.

    SQLite has very limited support for ALTER statements.
    """

    def _test_drop(self, column: str):
        self.insert_row()

        Band.alter().drop_column(column).run_sync()

        response = Band.raw("SELECT * FROM band").run_sync()

        column_names = response[0].keys()
        self.assertTrue("popularity" not in column_names)

    def test_drop_string(self):
        self._test_drop(Band.popularity)

    def test_drop_column(self):
        self._test_drop("popularity")


class TestAdd(DBTestCase):
    def test_add(self):
        """
        This needs a lot more work. Need to set values for existing rows.

        Just write the test for now ...
        """
        self.insert_row()

        add_query = Band.alter().add_column("weight", Integer(null=True))
        add_query.run_sync()

        response = Band.raw("SELECT * FROM band").run_sync()

        column_names = response[0].keys()
        self.assertTrue("weight" in column_names)

        self.assertEqual(response[0]["weight"], None)


@postgres_only
class TestUnique(DBTestCase):
    def test_unique(self):
        unique_query = Manager.alter().set_unique(Manager.name, True)
        unique_query.run_sync()

        Manager(name="Bob").save().run_sync()

        # Make sure non-unique names work:
        Manager(name="Sally").save().run_sync()

        # Check there's a unique row error ...
        with self.assertRaises(Exception):
            Manager(name="Bob").save().run_sync()

        response = Manager.select().run_sync()
        self.assertTrue(len(response) == 2)

        # Now remove the constraint, and add a row.
        not_unique_query = Manager.alter().set_unique(Manager.name, False)
        not_unique_query.run_sync()
        Manager(name="Bob").save().run_sync()

        response = Manager.select().run_sync()
        self.assertTrue(len(response), 2)


# TODO - make it work for SQLite. Should work.
@postgres_only
class TestMultiple(DBTestCase):
    """
    Make sure multiple alter statements work correctly.
    """

    def test_multiple(self):
        self.insert_row()

        query = (
            Manager.alter()
            .add_column("column_a", Integer(default=0, null=True))
            .add_column("column_b", Integer(default=0, null=True))
        )
        query.run_sync()

        response = Band.raw("SELECT * FROM manager").run_sync()

        column_names = response[0].keys()
        self.assertTrue("column_a" in column_names)
        self.assertTrue("column_b" in column_names)


class TestNull(DBTestCase):
    def test_null(self):
        pass


###############################################################################


class Ticket(Table):
    price = Numeric(digits=(5, 2))


@postgres_only
class TestSetDigits(TestCase):
    def setUp(self):
        Ticket.create_table().run_sync()

    def tearDown(self):
        Ticket.alter().drop_table().run_sync()

    def test_set_digits(self):
        Ticket.alter().set_digits(
            column=Ticket.price, digits=(6, 2)
        ).run_sync()

        Ticket.insert(Ticket(price=decimal.Decimal("9999.00"))).run_sync()
        ticket = Ticket.objects().first().run_sync()
        self.assertTrue(ticket.price == decimal.Decimal("9999.00"))
