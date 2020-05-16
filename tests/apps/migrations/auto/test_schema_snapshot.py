from unittest import TestCase

from piccolo.apps.migrations.auto import SchemaSnapshot, MigrationManager


class TestSchemaSnaphot(TestCase):
    def test_add_table(self):
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

    def test_drop_table(self):
        """
        Test dropping tables.
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

    def test_add_column(self):
        """
        Test adding columns.
        """
        manager = MigrationManager()
        manager.add_table(class_name="Manager", tablename="manager")
        manager.add_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="name",
            column_class_name="Varchar",
            params={"length": 100},
        )

        schema_snapshot = SchemaSnapshot(managers=[manager])
        snapshot = schema_snapshot.get_snapshot()

        self.assertTrue(len(snapshot) == 1)
        self.assertTrue(len(snapshot[0].columns) == 1)

    def test_rename_column(self):
        """
        Test renaming columns.
        """
        manager_1 = MigrationManager()
        manager_1.add_table(class_name="Manager", tablename="manager")
        manager_1.add_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="name",
            column_class_name="Varchar",
            params={"length": 100},
        )

        manager_2 = MigrationManager()
        manager_2.rename_column(
            table_class_name="Manager",
            tablename="manager",
            old_column_name="name",
            new_column_name="title",
        )

        schema_snapshot = SchemaSnapshot(managers=[manager_1, manager_2])
        snapshot = schema_snapshot.get_snapshot()
        self.assertTrue(snapshot[0].columns[0]._meta.name == "title")

        # Make sure double renames still work
        manager_3 = MigrationManager()
        manager_3.rename_column(
            table_class_name="Manager",
            tablename="manager",
            old_column_name="title",
            new_column_name="label",
        )

        schema_snapshot = SchemaSnapshot(
            managers=[manager_1, manager_2, manager_3]
        )
        snapshot = schema_snapshot.get_snapshot()
        self.assertTrue(snapshot[0].columns[0]._meta.name == "label")

    def test_alter_column(self):
        """
        Test altering columns.
        """
        manager_1 = MigrationManager()
        manager_1.add_table(class_name="Manager", tablename="manager")
        manager_1.add_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="name",
            column_class_name="Varchar",
            params={"length": 100},
        )

        manager_2 = MigrationManager()
        manager_2.alter_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="name",
            params={"unique": True},
            old_params={"unique": False},
        )

        schema_snapshot = SchemaSnapshot(managers=[manager_1, manager_2])
        snapshot = schema_snapshot.get_snapshot()

        self.assertTrue(snapshot[0].columns[0]._meta.unique)

    def test_get_table_from_snapshot(self):
        manager_1 = MigrationManager()
        manager_1.add_table(class_name="Manager", tablename="manager")
        manager_1.add_table(class_name="Band", tablename="band")

        schema_snapshot = SchemaSnapshot(managers=[manager_1])
        table = schema_snapshot.get_table_from_snapshot("Manager")

        self.assertTrue(table.class_name == "Manager")

        with self.assertRaises(ValueError):
            schema_snapshot.get_table_from_snapshot("Foo")
