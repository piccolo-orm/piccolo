import typing as t
from unittest import TestCase

from piccolo.columns import Varchar
from piccolo.table import Table
from piccolo.tablestorage import TableStorage
from piccolo.utils.sync import run_sync
from tests.base import postgres_only
from tests.example_apps.music.tables import Band, Manager


@postgres_only
class TestTableStorage(TestCase):
    def setUp(self) -> None:
        for table_class in (Manager, Band):
            table_class.create_table().run_sync()

    def tearDown(self):
        for table_class in (Band, Manager):
            table_class.alter().drop_table(if_exists=True).run_sync()

    def _compare_table_columns(
        self, table_1: t.Type[Table], table_2: t.Type[Table]
    ):
        """
        Make sure that for each column in table_1, there is a corresponding
        column in table_2 of the same type.
        """
        column_names = [
            column._meta.name for column in table_1._meta.non_default_columns
        ]
        for column_name in column_names:
            col_1 = table_1._meta.get_column_by_name(column_name)
            col_2 = table_2._meta.get_column_by_name(column_name)

            # Make sure they're the same type
            self.assertEqual(type(col_1), type(col_2))

            # Make sure they're both nullable or not
            self.assertEqual(col_1._meta.null, col_2._meta.null)

            # Make sure the max length is the same
            if isinstance(col_1, Varchar) and isinstance(col_2, Varchar):
                self.assertEqual(col_1.length, col_2.length)

            # Make sure the unique constraint is the same
            self.assertEqual(col_1._meta.unique, col_2._meta.unique)

    def test_reflect_all_tables(self):
        table_storage = TableStorage()
        table_storage.clear()
        run_sync(table_storage.reflect())
        reflected_tables = table_storage.tables
        self.assertEqual(len(reflected_tables), 2)
        for table_class in (Manager, Band):
            self._compare_table_columns(
                reflected_tables[table_class._meta.tablename], table_class
            )

    def test_reflect_with_include(self):
        table_storage = TableStorage()
        table_storage.clear()
        run_sync(table_storage.reflect(include=["manager"]))
        reflected_tables = table_storage.tables
        self.assertEqual(len(reflected_tables), 1)
        self._compare_table_columns(reflected_tables["manager"], Manager)

    def test_reflect_with_exclude(self):
        table_storage = TableStorage()
        table_storage.clear()
        run_sync(table_storage.reflect(exclude=["band"]))
        reflected_tables = table_storage.tables
        self.assertEqual(len(reflected_tables), 1)
        self._compare_table_columns(reflected_tables["manager"], Manager)
