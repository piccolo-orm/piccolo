import datetime
from unittest import TestCase

from piccolo.columns import Boolean, Timestamp, Varchar
from piccolo.table import Table


class StartedOnMixin(Table):
    """
    A mixin which inherits from Table.
    """

    started_on = Timestamp()


class FavouriteMixin:
    """
    A mixin which deliberately doesn't inherit from Table.
    """

    favourite = Boolean()


class Manager(StartedOnMixin, FavouriteMixin, Table):
    name = Varchar()


class ManagerA(StartedOnMixin, Table):
    name = Varchar()


class ManagerB(StartedOnMixin, Table):
    name = Varchar()


class TestInheritance(TestCase):
    """
    Make sure columns can be inheritted from parent classes.
    """

    def setUp(self):
        Manager.create_table().run_sync()

    def tearDown(self):
        Manager.alter().drop_table().run_sync()

    def test_inheritance(self):
        """
        Test that a table created via inheritance works as expected.
        """
        # Make sure both columns can be retrieved:
        for column_name in ("started_on", "name", "favourite"):
            Manager._meta.get_column_by_name(column_name)

        # Test saving and retrieving data:
        started_on = datetime.datetime(year=1989, month=12, day=1)
        name = "Guido"
        favourite = True
        Manager(
            name=name, started_on=started_on, favourite=favourite
        ).save().run_sync()

        response = Manager.select().first().run_sync()
        self.assertEqual(response["started_on"], started_on)
        self.assertEqual(response["name"], name)
        self.assertEqual(response["favourite"], favourite)


class TestRepeatedMixin(TestCase):
    """
    Make sure that if a mixin is used multiple times (i.e. across several
    Table classes), that it still works as expected.
    """

    def setUp(self):
        ManagerA.create_table().run_sync()
        ManagerB.create_table().run_sync()

    def tearDown(self):
        ManagerA.alter().drop_table().run_sync()
        ManagerB.alter().drop_table().run_sync()

    def test_inheritance(self):
        """
        Make sure both tables work as expected (they both inherit from the
        same mixin).
        """
        # Make sure the columns can be retrieved from both tables:
        for column_name in ("started_on", "name"):
            for Table_ in (ManagerA, ManagerB):
                Table_._meta.get_column_by_name(column_name)

        # Test saving and retrieving data:
        started_on = datetime.datetime(year=1989, month=12, day=1)
        name = "Guido"

        for _Table in (ManagerA, ManagerB):
            _Table(name=name, started_on=started_on).save().run_sync()

            response = _Table.select().first().run_sync()
            self.assertEqual(response["started_on"], started_on)
            self.assertEqual(response["name"], name)

        # Make sure the tables have the correct tablenames still.
        self.assertEqual(ManagerA._meta.tablename, "manager_a")
        self.assertEqual(ManagerB._meta.tablename, "manager_b")
