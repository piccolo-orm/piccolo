import time
from unittest import TestCase

from piccolo.columns import Column, ForeignKey, LazyTableReference, Varchar
from piccolo.columns.base import OnDelete, OnUpdate
from piccolo.table import Table
from tests.base import postgres_only
from tests.example_apps.music.tables import Band, Concert, Manager, Ticket


class Manager1(Table, tablename="manager"):
    name = Varchar()
    manager = ForeignKey("self", null=True)


class Band1(Table, tablename="band"):
    manager = ForeignKey(references=Manager1)


class Band2(Table, tablename="band"):
    manager = ForeignKey(references="Manager1")


class Band3(Table, tablename="band"):
    manager = ForeignKey(
        references=LazyTableReference(
            table_class_name="Manager1",
            module_path="tests.columns.test_foreignkey",
        )
    )


class Band4(Table, tablename="band"):
    manager = ForeignKey(references="tests.columns.test_foreignkey.Manager1")


class Band5(Table):
    """
    Contains a ForeignKey with non-default `on_delete` and `on_update` values.
    """

    manager = ForeignKey(
        references=Manager,
        on_delete=OnDelete.set_null,
        on_update=OnUpdate.set_null,
    )


class TestForeignKeyMeta(TestCase):
    """
    Make sure that `ForeignKeyMeta` is setup correctly.
    """

    def test_foreignkeymeta(self):
        self.assertTrue(
            Band5.manager._foreign_key_meta.on_update == OnUpdate.set_null
        )
        self.assertTrue(
            Band5.manager._foreign_key_meta.on_delete == OnDelete.set_null
        )
        self.assertTrue(Band.manager._foreign_key_meta.references == Manager)


@postgres_only
class TestOnDeleteOnUpdate(TestCase):
    """
    Make sure that on_delete, and on_update are correctly applied in the
    database.
    """

    def setUp(self):
        for table_class in (Manager, Band5):
            table_class.create_table().run_sync()

    def tearDown(self):
        for table_class in (Band5, Manager):
            table_class.alter().drop_table(if_exists=True).run_sync()

    def test_on_delete_on_update(self):
        response = Band5.raw(
            """
            SELECT
                rc.update_rule AS on_update,
                rc.delete_rule AS on_delete
            FROM information_schema.table_constraints tc
            LEFT JOIN information_schema.key_column_usage kcu
                ON tc.constraint_catalog = kcu.constraint_catalog
                AND tc.constraint_schema = kcu.constraint_schema
                AND tc.constraint_name = kcu.constraint_name
            LEFT JOIN information_schema.referential_constraints rc
                ON tc.constraint_catalog = rc.constraint_catalog
                AND tc.constraint_schema = rc.constraint_schema
                AND tc.constraint_name = rc.constraint_name
            WHERE
                lower(tc.constraint_type) in ('foreign key')
                AND tc.table_name = 'band5'
                AND kcu.column_name = 'manager';
            """
        ).run_sync()
        self.assertTrue(response[0]["on_update"] == "SET NULL")
        self.assertTrue(response[0]["on_delete"] == "SET NULL")


class TestForeignKeySelf(TestCase):
    """
    Test that ForeignKey columns can be created with references to the parent
    table.
    """

    def setUp(self):
        Manager1.create_table().run_sync()

    def test_foreign_key_self(self):
        manager = Manager1(name="Mr Manager")
        manager.save().run_sync()

        worker = Manager1(name="Mr Worker", manager=manager.id)
        worker.save().run_sync()

        response = (
            Manager1.select(Manager1.name, Manager1.manager.name)
            .order_by(Manager1.name)
            .run_sync()
        )
        self.assertEqual(
            response,
            [
                {"name": "Mr Manager", "manager.name": None},
                {"name": "Mr Worker", "manager.name": "Mr Manager"},
            ],
        )

    def tearDown(self):
        Manager1.alter().drop_table().run_sync()


class TestForeignKeyString(TestCase):
    """
    Test that ForeignKey columns can be created with a `references` argument
    set as a string value.
    """

    def setUp(self):
        Manager1.create_table().run_sync()

    def test_foreign_key_string(self):
        Band2.create_table().run_sync()
        self.assertEqual(
            Band2.manager._foreign_key_meta.resolved_references,
            Manager1,
        )
        Band2.alter().drop_table().run_sync()

        Band4.create_table().run_sync()
        self.assertEqual(
            Band4.manager._foreign_key_meta.resolved_references,
            Manager1,
        )
        Band4.alter().drop_table().run_sync()

    def tearDown(self):
        Manager1.alter().drop_table().run_sync()


class TestForeignKeyRelativeError(TestCase):
    def test_foreign_key_relative_error(self):
        """
        Make sure that a references argument which contains a relative module
        isn't allowed.
        """
        with self.assertRaises(ValueError) as manager:

            class BandRelative(Table, tablename="band"):
                manager = ForeignKey("..example_app.tables.Manager", null=True)

        self.assertEqual(
            manager.exception.__str__(), "Relative imports aren't allowed"
        )


class TestReferences(TestCase):
    def test_foreign_key_references(self):
        """
        Make sure foreign key references are stored correctly on the table
        which is the target of the ForeignKey.
        """
        self.assertEqual(len(Manager1._meta.foreign_key_references), 5)

        self.assertTrue(Band1.manager in Manager._meta.foreign_key_references)
        self.assertTrue(Band2.manager in Manager._meta.foreign_key_references)
        self.assertTrue(Band3.manager in Manager._meta.foreign_key_references)
        self.assertTrue(Band4.manager in Manager._meta.foreign_key_references)
        self.assertTrue(
            Manager1.manager in Manager1._meta.foreign_key_references
        )


class TestLazyTableReference(TestCase):
    def test_lazy_reference_to_app(self):
        """
        Make sure a LazyTableReference to a Table within a Piccolo app works.
        """
        reference = LazyTableReference(
            table_class_name="Manager", app_name="example_app"
        )
        self.assertTrue(reference.resolve() is Manager)


class TestAttributeAccess(TestCase):
    def test_attribute_access(self):
        """
        Make sure that attribute access still works correctly with lazy
        references.
        """
        self.assertTrue(isinstance(Band1.manager.name, Varchar))
        self.assertTrue(isinstance(Band2.manager.name, Varchar))
        self.assertTrue(isinstance(Band3.manager.name, Varchar))
        self.assertTrue(isinstance(Band4.manager.name, Varchar))

    def test_recursion_limit(self):
        """
        When a table has a ForeignKey to itself, an Exception should be raised
        if the call chain is too large.
        """
        # Should be fine:
        column: Column = Manager1.manager.name
        self.assertTrue(len(column._meta.call_chain), 1)
        self.assertTrue(isinstance(column, Varchar))

        with self.assertRaises(Exception):
            Manager1.manager.manager.manager.manager.manager.manager.manager.manager.manager.manager.manager.name  # noqa

    def test_recursion_time(self):
        """
        Make sure that a really large call chain doesn't take too long.
        """
        start = time.time()
        Manager1.manager.manager.manager.manager.manager.manager.name
        end = time.time()
        self.assertTrue(end - start < 1.0)


class TestAllColumns(TestCase):
    def test_all_columns(self):
        """
        Make sure you can retrieve all columns from a related table, without
        explicitly specifying them.
        """
        all_columns = Band.manager.all_columns()
        self.assertEqual(all_columns, [Band.manager.id, Band.manager.name])

        # Make sure the call chains are also correct.
        self.assertEqual(
            all_columns[0]._meta.call_chain, Band.manager.id._meta.call_chain
        )
        self.assertEqual(
            all_columns[1]._meta.call_chain, Band.manager.name._meta.call_chain
        )

    def test_all_columns_deep(self):
        """
        Make sure ``all_columns`` works when the joins are several layers deep.
        """
        all_columns = Concert.band_1.manager.all_columns()
        self.assertEqual(all_columns, [Band.manager.id, Band.manager.name])

        # Make sure the call chains are also correct.
        self.assertEqual(
            all_columns[0]._meta.call_chain,
            Concert.band_1.manager.id._meta.call_chain,
        )
        self.assertEqual(
            all_columns[1]._meta.call_chain,
            Concert.band_1.manager.name._meta.call_chain,
        )

    def test_all_columns_exclude(self):
        """
        Make sure you can exclude some columns.
        """
        self.assertEqual(
            Band.manager.all_columns(exclude=["id"]), [Band.manager.name]
        )

        self.assertEqual(
            Band.manager.all_columns(exclude=[Band.manager.id]),
            [Band.manager.name],
        )


class TestAllRelated(TestCase):
    def test_all_related(self):
        """
        Make sure you can retrieve all foreign keys from a related table,
        without explicitly specifying them.
        """
        all_related = Ticket.concert.all_related()

        self.assertEqual(
            all_related,
            [
                Ticket.concert.band_1,
                Ticket.concert.band_2,
                Ticket.concert.venue,
            ],
        )

        # Make sure the call chains are also correct.
        self.assertEqual(
            all_related[0]._meta.call_chain,
            Ticket.concert.band_1._meta.call_chain,
        )
        self.assertEqual(
            all_related[1]._meta.call_chain,
            Ticket.concert.band_2._meta.call_chain,
        )
        self.assertEqual(
            all_related[2]._meta.call_chain,
            Ticket.concert.venue._meta.call_chain,
        )

    def test_all_related_deep(self):
        """
        Make sure ``all_related`` works when the joins are several layers deep.
        """
        all_related = Ticket.concert.band_1.all_related()
        self.assertEqual(all_related, [Ticket.concert.band_1.manager])

        # Make sure the call chains are also correct.
        self.assertEqual(
            all_related[0]._meta.call_chain,
            Ticket.concert.band_1.manager._meta.call_chain,
        )

    def test_all_related_exclude(self):
        """
        Make sure you can exclude some columns.
        """
        self.assertEqual(
            Ticket.concert.all_related(exclude=["venue"]),
            [Ticket.concert.band_1, Ticket.concert.band_2],
        )

        self.assertEqual(
            Ticket.concert.all_related(exclude=[Ticket.concert.venue]),
            [Ticket.concert.band_1, Ticket.concert.band_2],
        )
