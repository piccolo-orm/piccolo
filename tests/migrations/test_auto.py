from unittest import TestCase

from piccolo.migrations.auto import (
    SchemaSnapshot,
    MigrationManager,
    compare_dicts,
)


class TestCompareDicts(TestCase):
    def test_compare_dicts(self):
        dict_1 = {"a": 1, "b": 2}
        dict_2 = {"a": 1, "b": 3}
        response = compare_dicts(dict_1, dict_2)
        self.assertEqual(response, {"b": 2})


class TestSchemaSnaphot(TestCase):
    def test_snapshot_add(self):
        """
        Test adding tables.
        """
        manager_1 = MigrationManager()
        manager_1.add_table(class_name="Manager", tablename="manager")

        manager_2 = MigrationManager()
        manager_2.add_table(class_name="Band", tablename="band")

        schema_snapshot = SchemaSnapshot(managers=[manager_1, manager_2])
        snapshot = schema_snapshot.get_snapshot()

        self.assertTrue(len(snapshot) == 2)

        class_names = [i.class_name for i in snapshot]
        self.assertTrue("Band" in class_names)
        self.assertTrue("Manager" in class_names)

    def test_snapshot_remove(self):
        """
        Test adding and removing tables.
        """
        manager_1 = MigrationManager()
        manager_1.add_table(class_name="Manager", tablename="manager")
        manager_1.add_table(class_name="Band", tablename="band")

        manager_2 = MigrationManager()
        manager_2.drop_table(class_name="Band", tablename="band")

        schema_snapshot = SchemaSnapshot(managers=[manager_1, manager_2])
        snapshot = schema_snapshot.get_snapshot()

        self.assertTrue(len(snapshot) == 1)

        class_names = [i.class_name for i in snapshot]
        self.assertTrue("Manager" in class_names)

    def test_add_columns(self):
        """
        Test adding and removing tables.
        """
        manager_1 = MigrationManager()
        manager_1.add_table(class_name="Manager", tablename="manager")
        manager_1.add_column(
            table_class_name="Manager",
            column_name="name",
            column_class_name="Varchar",
            params={"length": 100},
        )

        schema_snapshot = SchemaSnapshot(managers=[manager_1])
        snapshot = schema_snapshot.get_snapshot()

        self.assertTrue(len(snapshot) == 1)
        self.assertTrue(len(snapshot[0].columns) == 1)

    def test_alter_columns(self):
        """
        Test altering columns.
        """
        manager_1 = MigrationManager()
        manager_1.add_table(class_name="Manager", tablename="manager")
        manager_1.add_column(
            table_class_name="Manager",
            column_name="name",
            column_class_name="Varchar",
            params={"length": 100},
        )

        manager_2 = MigrationManager()
        manager_2.alter_column(
            table_class_name="Manager",
            column_name="name",
            params={"unique": True},
        )

        schema_snapshot = SchemaSnapshot(managers=[manager_1, manager_2])
        snapshot = schema_snapshot.get_snapshot()

        self.assertTrue(snapshot[0].columns[0]._meta.unique)
