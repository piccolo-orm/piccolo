from unittest import TestCase

from piccolo.columns import ForeignKey, Varchar
from piccolo.columns.base import OnDelete, OnUpdate
from piccolo.table import Table
from tests.base import postgres_only


class Manager(Table):
    name = Varchar()


class Band(Table):
    """
    Contains a ForeignKey with non-default `on_delete` and `on_update` values.
    """

    manager = ForeignKey(
        references=Manager,
        on_delete=OnDelete.set_null,
        on_update=OnUpdate.set_null,
    )


@postgres_only
class TestOnDeleteOnUpdate(TestCase):
    """
    Make sure that on_delete, and on_update are correctly applied in the
    database.
    """

    def setUp(self):
        for table_class in (Manager, Band):
            table_class.create_table().run_sync()

    def tearDown(self):
        for table_class in (Band, Manager):
            table_class.alter().drop_table(if_exists=True).run_sync()

    def test_on_delete_on_update(self):
        response = Band.raw(
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
                AND tc.table_name = 'band'
                AND kcu.column_name = 'manager';
            """
        ).run_sync()
        self.assertTrue(response[0]["on_update"] == "SET NULL")
        self.assertTrue(response[0]["on_delete"] == "SET NULL")
