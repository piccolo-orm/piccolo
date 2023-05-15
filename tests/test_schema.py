from unittest import TestCase

from piccolo.schema import SchemaManager
from piccolo.table import Table


class Band(Table, schema="schema_1"):
    pass


class TestListTables(TestCase):
    def setUp(self):
        Band.create_table().run_sync()

    def tearDown(self):
        Band.alter().drop_table().run_sync()

    def test_list_tables(self):
        """
        Make sure we can list all the tables in a schema.
        """
        table_list = (
            SchemaManager()
            .list_tables(schema_name=Band._meta.schema)
            .run_sync()
        )
        self.assertListEqual(table_list, [Band._meta.tablename])


class TestCreateAndDrop(TestCase):
    def test_create_and_drop(self):
        """
        Make sure a schema can be created, and dropped.
        """
        manager = SchemaManager()

        # Make sure schema names with spaces, and clashing with keywords work.
        for schema_name in ("test_schema", "test schema", "user"):
            manager.create_schema(schema_name=schema_name).run_sync()

            self.assertIn(schema_name, manager.list_schemas().run_sync())

            manager.drop_schema(schema_name=schema_name).run_sync()
            self.assertNotIn(schema_name, manager.list_schemas().run_sync())


class TestMoveTable(TestCase):

    new_schema = "schema_2"

    def setUp(self):
        Band.create_table(if_not_exists=True).run_sync()
        SchemaManager().create_schema(
            self.new_schema, if_not_exists=True
        ).run_sync()

    def tearDown(self):
        Band.alter().drop_table(if_exists=True).run_sync()
        SchemaManager().drop_schema(
            self.new_schema, if_exists=True, cascade=True
        ).run_sync()

    def test_move_table(self):
        """
        Make sure we can move a table to a different schema.
        """
        manager = SchemaManager()

        manager.move_table(
            table_name=Band._meta.tablename,
            new_schema=self.new_schema,
            current_schema=Band._meta.schema,
        ).run_sync()

        self.assertIn(
            Band._meta.tablename,
            manager.list_tables(schema_name=self.new_schema).run_sync(),
        )

        self.assertNotIn(
            Band._meta.tablename,
            manager.list_tables(schema_name="schema_1").run_sync(),
        )


class TestDDL(TestCase):
    manager = SchemaManager()

    def test_create_schema(self):
        self.assertEqual(
            self.manager.create_schema(
                schema_name="schema_1", if_not_exists=False
            ).ddl,
            'CREATE SCHEMA "schema_1"',
        )

        self.assertEqual(
            self.manager.create_schema(
                schema_name="schema_1", if_not_exists=True
            ).ddl,
            'CREATE SCHEMA IF NOT EXISTS "schema_1"',
        )

    def test_drop_schema(self):
        self.assertEqual(
            self.manager.drop_schema(
                schema_name="schema_1", if_exists=False
            ).ddl,
            'DROP SCHEMA "schema_1"',
        )

        self.assertEqual(
            self.manager.drop_schema(
                schema_name="schema_1", if_exists=True
            ).ddl,
            'DROP SCHEMA IF EXISTS "schema_1"',
        )

        self.assertEqual(
            self.manager.drop_schema(
                schema_name="schema_1", if_exists=True, cascade=True
            ).ddl,
            'DROP SCHEMA IF EXISTS "schema_1" CASCADE',
        )

        self.assertEqual(
            self.manager.drop_schema(
                schema_name="schema_1", if_exists=False, cascade=True
            ).ddl,
            'DROP SCHEMA "schema_1" CASCADE',
        )

    def test_move_table(self):
        self.assertEqual(
            self.manager.move_table(
                table_name="band",
                new_schema="schema_2",
                current_schema="schema_1",
            ).ddl,
            'ALTER TABLE "schema_1"."band" SET SCHEMA "schema_2"',
        )

        self.assertEqual(
            self.manager.move_table(
                table_name="band",
                new_schema="schema_2",
            ).ddl,
            'ALTER TABLE "band" SET SCHEMA "schema_2"',
        )
