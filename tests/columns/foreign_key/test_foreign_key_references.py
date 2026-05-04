from unittest import TestCase

from piccolo.columns import ForeignKey, Varchar
from piccolo.table import Table


class Manager(Table, tablename="manager_fk_references_test"):
    name = Varchar()


class BandA(Table):
    manager = ForeignKey(references=Manager)


class BandB(Table):
    manager: ForeignKey["Manager"] = ForeignKey(references="Manager")


class TestReferences(TestCase):
    def test_foreign_key_references(self):
        """
        Make sure foreign key references are stored correctly on the table
        which is the target of the ForeignKey.
        """
        self.assertEqual(len(Manager._meta.foreign_key_references), 2)

        self.assertTrue(BandA.manager in Manager._meta.foreign_key_references)
        self.assertTrue(BandB.manager in Manager._meta.foreign_key_references)
