import uuid
from unittest import TestCase

from piccolo.columns.column_types import UUID, ForeignKey, Serial, Varchar
from piccolo.table import Table


class MyTableDefaultPrimaryKey(Table):
    name = Varchar()


class MyTablePrimaryKeySerial(Table):
    pk = Serial(null=False, primary_key=True)
    name = Varchar()


class MyTablePrimaryKeyUUID(Table):
    id = UUID(null=False, primary_key=True)
    name = Varchar()


class TestPrimaryKeyDefault(TestCase):
    def setUp(self):
        MyTableDefaultPrimaryKey.create_table().run_sync()

    def tearDown(self):
        MyTableDefaultPrimaryKey.alter().drop_table().run_sync()

    def test_return_type(self):
        row = MyTableDefaultPrimaryKey()
        row.save().run_sync()

        self.assertIsInstance(row._meta.primary_key, Serial)


class TestPrimaryKeyInteger(TestCase):
    def setUp(self):
        MyTablePrimaryKeySerial.create_table().run_sync()

    def tearDown(self):
        MyTablePrimaryKeySerial.alter().drop_table().run_sync()

    def test_return_type(self):
        row = MyTablePrimaryKeySerial()
        result = row.save().run_sync()[0]

        self.assertIsInstance(result["pk"], int)


class TestPrimaryKeyUUID(TestCase):
    def setUp(self):
        MyTablePrimaryKeyUUID.create_table().run_sync()

    def tearDown(self):
        MyTablePrimaryKeyUUID.alter().drop_table().run_sync()

    def test_return_type(self):
        row = MyTablePrimaryKeyUUID()
        row.save().run_sync()

        self.assertIsInstance(row.id, uuid.UUID)


class Manager(Table):
    pk = UUID(primary=True, key=True)
    name = Varchar()


class Band(Table):
    pk = UUID(primary=True, key=True)
    name = Varchar()
    manager = ForeignKey(Manager)


class TestPrimaryKeyQueries(TestCase):
    def setUp(self):
        Manager.create_table().run_sync()
        Band.create_table().run_sync()

    def tearDown(self):
        Band.alter().drop_table().run_sync()
        Manager.alter().drop_table().run_sync()

    def test_primary_key_queries(self):
        """
        An assortment of queries to make sure that tables with a custom primary
        key column defined work as expected.
        """
        Manager.insert(
            Manager(name="Guido"),
            Manager(name="Graydon"),
        ).run_sync()

        #######################################################################
        # Make sure they've been saved in the database, and the return types
        # are correct

        self.assertTrue(
            Manager.select(Manager.name)
            .output(as_list=True)
            .order_by(Manager.name)
            .run_sync(),
            ["Guido", "Graydon"],
        )

        manager_dict = Manager.select().first().run_sync()

        self.assertEqual(
            [i for i in manager_dict.keys()],
            ["pk", "name"],
        )

        self.assertTrue(isinstance(manager_dict["pk"], uuid.UUID))

        #######################################################################
        # Make sure we can create rows with foreign keys to tables with a
        # custom primary key column.

        manager = Manager.objects().first().run_sync()

        band = Band(manager=manager, name="Pythonistas")
        band.save().run_sync()

        band_dict = Band.select().first().run_sync()

        self.assertEqual(
            [i for i in band_dict.keys()], ["pk", "name", "manager"]
        )
        self.assertTrue(isinstance(band_dict["pk"], uuid.UUID))
        self.assertTrue(isinstance(band_dict["manager"], uuid.UUID))

        #######################################################################
        # Make sure foreign key values can be specified as the primary key's
        # type (i.e. `uuid.UUID`).

        manager = Manager.objects().first().run_sync()

        band_2 = Band(manager=manager.pk, name="Pythonistas 2")
        band_2.save().run_sync()

        self.assertEqual(
            Band.select(Band.name)
            .output(as_list=True)
            .order_by(Band.name)
            .run_sync(),
            ["Pythonistas", "Pythonistas 2"],
        )

        #######################################################################
        # Make sure `get_related` works

        self.assertEqual(
            band_2.get_related(Band.manager).run_sync().pk, manager.pk
        )

        #######################################################################
        # Make sure `remove` works

        band_2.remove().run_sync()

        self.assertEqual(
            Band.select(Band.name)
            .output(as_list=True)
            .order_by(Band.name)
            .run_sync(),
            ["Pythonistas"],
        )
