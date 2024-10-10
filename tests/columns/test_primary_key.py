import uuid

from piccolo.columns.column_types import (
    UUID,
    BigSerial,
    ForeignKey,
    Serial,
    Varchar,
)
from piccolo.table import Table
from piccolo.testing.test_case import TableTest


class MyTableDefaultPrimaryKey(Table):
    name = Varchar()


class MyTablePrimaryKeySerial(Table):
    pk = Serial(null=False, primary_key=True)
    name = Varchar()


class MyTablePrimaryKeyBigSerial(Table):
    pk = BigSerial(null=False, primary_key=True)
    name = Varchar()


class MyTablePrimaryKeyUUID(Table):
    pk = UUID(null=False, primary_key=True)
    name = Varchar()


class TestPrimaryKeyDefault(TableTest):
    tables = [MyTableDefaultPrimaryKey]

    def test_return_type(self):
        row = MyTableDefaultPrimaryKey()
        row.save().run_sync()

        self.assertIsInstance(row._meta.primary_key, Serial)
        self.assertIsInstance(row["id"], int)


class TestPrimaryKeyInteger(TableTest):
    tables = [MyTablePrimaryKeySerial]

    def test_return_type(self):
        row = MyTablePrimaryKeySerial()
        row.save().run_sync()

        self.assertIsInstance(row._meta.primary_key, Serial)
        self.assertIsInstance(row["pk"], int)


class TestPrimaryKeyBigSerial(TableTest):
    tables = [MyTablePrimaryKeyBigSerial]

    def test_return_type(self):
        row = MyTablePrimaryKeyBigSerial()
        row.save().run_sync()

        self.assertIsInstance(row._meta.primary_key, BigSerial)
        self.assertIsInstance(row["pk"], int)


class TestPrimaryKeyUUID(TableTest):
    tables = [MyTablePrimaryKeyUUID]

    def test_return_type(self):
        row = MyTablePrimaryKeyUUID()
        row.save().run_sync()

        self.assertIsInstance(row._meta.primary_key, UUID)
        self.assertIsInstance(row["pk"], uuid.UUID)


class Manager(Table):
    pk = UUID(primary=True, key=True)
    name = Varchar()


class Band(Table):
    pk = UUID(primary=True, key=True)
    name = Varchar()
    manager = ForeignKey(Manager)


class TestPrimaryKeyQueries(TableTest):
    tables = [Manager, Band]

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
        assert manager_dict is not None

        self.assertEqual(
            [i for i in manager_dict.keys()],
            ["pk", "name"],
        )

        self.assertIsInstance(manager_dict["pk"], uuid.UUID)

        #######################################################################
        # Make sure we can create rows with foreign keys to tables with a
        # custom primary key column.

        manager = Manager.objects().first().run_sync()

        band = Band(manager=manager, name="Pythonistas")
        band.save().run_sync()

        band_dict = Band.select().first().run_sync()
        assert band_dict is not None

        self.assertEqual(
            [i for i in band_dict.keys()], ["pk", "name", "manager"]
        )
        self.assertIsInstance(band_dict["pk"], uuid.UUID)
        self.assertIsInstance(band_dict["manager"], uuid.UUID)

        #######################################################################
        # Make sure foreign key values can be specified as the primary key's
        # type (i.e. `uuid.UUID`).

        manager = Manager.objects().first().run_sync()
        assert manager is not None

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

        manager_from_db = band_2.get_related(Band.manager).run_sync()
        assert manager_from_db is not None

        self.assertEqual(manager_from_db.pk, manager.pk)

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
