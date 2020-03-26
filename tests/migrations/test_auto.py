import asyncio
import typing as t
from unittest import TestCase

from piccolo.columns.column_types import Varchar
from piccolo.migrations.auto import (
    DiffableTable,
    SchemaDiffer,
    SchemaSnapshot,
    MigrationManager,
)
from piccolo.migrations.auto.diffable_table import compare_dicts

from ..base import DBTestCase


class TestCompareDicts(TestCase):
    def test_compare_dicts(self):
        dict_1 = {"a": 1, "b": 2}
        dict_2 = {"a": 1, "b": 3}
        response = compare_dicts(dict_1, dict_2)
        self.assertEqual(response, {"b": 2})


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
        )

        schema_snapshot = SchemaSnapshot(managers=[manager_1, manager_2])
        snapshot = schema_snapshot.get_snapshot()

        self.assertTrue(snapshot[0].columns[0]._meta.unique)


class TestSchemaDiffer(TestCase):
    def test_rename_table(self):
        """
        Test renaming a table.
        """
        name_column = Varchar()
        name_column._meta.name = "name"

        schema: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Act", tablename="act", columns=[name_column]
            )
        ]
        schema_snapshot: t.List[DiffableTable] = [
            DiffableTable(
                class_name="Band", tablename="band", columns=[name_column]
            )
        ]

        schema_differ = SchemaDiffer(
            schema=schema, schema_snapshot=schema_snapshot, auto_input="y"
        )

        self.assertTrue(len(schema_differ.rename_tables) == 1)
        self.assertEqual(
            schema_differ.rename_tables[0],
            "manager.rename_table(old_class_name='Band', new_class_name='Act', new_tablename='act')",  # noqa
        )

        self.assertEqual(schema_differ.create_tables, [])
        self.assertEqual(schema_differ.drop_tables, [])


class TestMigrationManager(DBTestCase):
    def test_rename_column(self):
        """
        Test running a MigrationManager which contains a column rename
        operation.
        """
        self.insert_row()

        manager = MigrationManager()
        manager.rename_column(
            table_class_name="Band",
            tablename="band",
            old_column_name="name",
            new_column_name="title",
        )
        asyncio.run(manager.run())

        response = self.run_sync("SELECT * FROM band;")
        self.assertTrue("title" in response[0].keys())
        self.assertTrue("name" not in response[0].keys())
