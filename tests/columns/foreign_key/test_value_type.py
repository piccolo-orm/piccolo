import uuid
from unittest import TestCase

from piccolo.columns import UUID, ForeignKey, Varchar
from piccolo.table import Table


class Manager(Table):
    name = Varchar()
    manager: ForeignKey["Manager"] = ForeignKey("self", null=True)


class Band(Table):
    manager = ForeignKey(references=Manager)


class ManagerUUID(Table):
    pk = UUID(primary_key=True)


class BandUUID(Table):
    manager = ForeignKey(references=ManagerUUID)


class TestValueType(TestCase):
    """
    The `value_type` of the `ForeignKey` should depend on the `PrimaryKey` of
    the referenced table.
    """

    def test_value_type(self):
        self.assertTrue(Band.manager.value_type is int)
        self.assertTrue(BandUUID.manager.value_type is uuid.UUID)
