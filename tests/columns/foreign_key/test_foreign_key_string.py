from unittest import TestCase

from piccolo.columns import ForeignKey, LazyTableReference, Varchar
from piccolo.table import Table


class Manager(Table):
    name = Varchar()


class BandA(Table):
    manager = ForeignKey(references="Manager")


class BandB(Table):
    manager = ForeignKey(
        references=LazyTableReference(
            table_class_name="Manager",
            module_path=__name__,
        )
    )


class BandC(Table, tablename="band"):
    manager = ForeignKey(references=f"{__name__}.Manager")


class TestForeignKeyString(TestCase):
    """
    Test that ForeignKey columns can be created with a `references` argument
    set as a string value.
    """

    def test_foreign_key_string(self):
        for band_table in (BandA, BandB, BandC):
            self.assertIs(
                band_table.manager._foreign_key_meta.resolved_references,
                Manager,
            )


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


class TestLazyTableReference(TestCase):
    def test_lazy_reference_to_app(self):
        """
        Make sure a LazyTableReference to a Table within a Piccolo app works.
        """
        from tests.example_apps.music.tables import Manager

        reference = LazyTableReference(
            table_class_name="Manager", app_name="music"
        )

        self.assertIs(reference.resolve(), Manager)
