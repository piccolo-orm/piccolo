from unittest import TestCase

from piccolo.columns import ForeignKey, Varchar
from piccolo.columns.base import OnDelete, OnUpdate
from piccolo.table import Table


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


class TestForeignKeyMeta(TestCase):
    """
    Make sure that `ForeignKeyMeta` is setup correctly.
    """

    def test_foreignkeymeta(self):
        self.assertTrue(
            Band.manager._foreign_key_meta.on_update == OnUpdate.set_null
        )
        self.assertTrue(
            Band.manager._foreign_key_meta.on_delete == OnDelete.set_null
        )
        self.assertTrue(Band.manager._foreign_key_meta.references == Manager)
