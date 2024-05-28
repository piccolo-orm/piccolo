import time
from unittest import TestCase

from piccolo.columns import Column, ForeignKey, LazyTableReference, Varchar
from piccolo.table import Table


class Manager(Table):
    name = Varchar()
    manager: ForeignKey["Manager"] = ForeignKey("self")


class BandA(Table):
    manager = ForeignKey(references=Manager)


class BandB(Table):
    manager: ForeignKey["Manager"] = ForeignKey(references="Manager")


class BandC(Table):
    manager: ForeignKey["Manager"] = ForeignKey(
        references=LazyTableReference(
            table_class_name="Manager",
            module_path=__name__,
        )
    )


class BandD(Table):
    manager: ForeignKey["Manager"] = ForeignKey(
        references=f"{__name__}.Manager"
    )


class TestAttributeAccess(TestCase):
    def test_attribute_access(self):
        """
        Make sure that attribute access still works correctly with lazy
        references.
        """
        for band_table in (BandA, BandB, BandC, BandD):
            self.assertIsInstance(band_table.manager.name, Varchar)

    def test_recursion_limit(self) -> None:
        """
        When a table has a ForeignKey to itself, an Exception should be raised
        if the call chain is too large.
        """
        # Should be fine:
        column: Column = Manager.manager.name
        self.assertTrue(len(column._meta.call_chain), 1)
        self.assertIsInstance(column, Varchar)

        with self.assertRaises(Exception):
            Manager.manager.manager.manager.manager.manager.manager.manager.manager.manager.manager.manager.name  # type: ignore  # noqa: E501

    def test_recursion_time(self):
        """
        Make sure that a really large call chain doesn't take too long.
        """
        start = time.time()
        Manager.manager._.manager._.manager._.manager._.manager._.manager._.name  # noqa: E501
        end = time.time()
        self.assertLess(end - start, 1.0)
