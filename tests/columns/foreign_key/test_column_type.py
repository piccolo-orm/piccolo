from unittest import TestCase

from piccolo.columns import (
    UUID,
    BigInt,
    BigSerial,
    ForeignKey,
    Integer,
    Serial,
    Varchar,
)
from piccolo.table import Table


class TestColumnType(TestCase):
    """
    The `column_type` of the `ForeignKey` should depend on the `PrimaryKey` of
    the referenced table.
    """

    def test_serial(self):
        class Manager(Table):
            id = Serial(primary_key=True)

        class Band(Table):
            manager = ForeignKey(Manager)

        self.assertEqual(
            Band.manager.column_type,
            Integer().column_type,
        )

    def test_bigserial(self):
        class Manager(Table):
            id = BigSerial(primary_key=True)

        class Band(Table):
            manager = ForeignKey(Manager)

        self.assertEqual(
            Band.manager.column_type,
            BigInt()._get_column_type(
                engine_type=Band.manager._meta.engine_type
            ),
        )

    def test_uuid(self):
        class Manager(Table):
            id = UUID(primary_key=True)

        class Band(Table):
            manager = ForeignKey(Manager)

        self.assertEqual(
            Band.manager.column_type,
            Manager.id.column_type,
        )

    def test_varchar(self):
        class Manager(Table):
            id = Varchar(primary_key=True)

        class Band(Table):
            manager = ForeignKey(Manager)

        self.assertEqual(
            Band.manager.column_type,
            Manager.id.column_type,
        )
