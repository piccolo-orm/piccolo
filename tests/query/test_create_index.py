from unittest import TestCase

from piccolo.columns.column_types import Varchar, Vector
from piccolo.columns.indexes import IndexMethod
from piccolo.query.methods.create_index import CreateIndex
from piccolo.table import Table
from tests.base import postgres_only, sqlite_only


class ItemTable(Table):
    embedding = Vector(dimensions=3)
    name = Varchar()


class TestIndexMethod(TestCase):

    def test_hnsw_exists(self):
        """
        Make sure the hnsw index method is available.
        """
        self.assertEqual(IndexMethod.hnsw.value, "hnsw")

    def test_ivfflat_exists(self):
        """
        Make sure the ivfflat index method is available.
        """
        self.assertEqual(IndexMethod.ivfflat.value, "ivfflat")


@postgres_only
class TestCreateIndexDDL(TestCase):

    def test_basic_ddl_unchanged(self):
        """
        Make sure existing DDL generation is unaffected when no
        operator_class or index_params are provided.
        """
        idx = CreateIndex(
            ItemTable, [ItemTable.name], method=IndexMethod.btree
        )
        ddl = idx.postgres_ddl[0]
        self.assertIn("USING btree", ddl)
        self.assertIn('"name"', ddl)
        self.assertNotIn("WITH", ddl)

    def test_operator_class(self):
        """
        Make sure the operator class is appended inside the column list
        parentheses when provided.
        """
        idx = CreateIndex(
            ItemTable,
            [ItemTable.name],
            method=IndexMethod.gin,
            operator_class="gin_trgm_ops",
        )
        ddl = idx.postgres_ddl[0]
        self.assertIn("USING gin", ddl)
        self.assertIn("gin_trgm_ops", ddl)
        self.assertNotIn("WITH", ddl)

    def test_hnsw_with_index_params(self):
        """
        Make sure the WITH clause is appended when index_params are provided,
        as required for HNSW indexes.
        """
        idx = CreateIndex(
            ItemTable,
            [ItemTable.embedding],
            method=IndexMethod.hnsw,
            operator_class="vector_cosine_ops",
            index_params={"m": 16, "ef_construction": 64},
        )
        ddl = idx.postgres_ddl[0]
        self.assertIn("USING hnsw", ddl)
        self.assertIn("vector_cosine_ops", ddl)
        self.assertIn("WITH (", ddl)
        self.assertIn("m=16", ddl)
        self.assertIn("ef_construction=64", ddl)

    def test_index_params_without_operator_class(self):
        """
        Make sure the WITH clause can be used without an operator class.
        """
        idx = CreateIndex(
            ItemTable,
            [ItemTable.name],
            method=IndexMethod.gin,
            index_params={"fastupdate": "off"},
        )
        ddl = idx.postgres_ddl[0]
        self.assertIn("WITH (fastupdate=off)", ddl)

    def test_if_not_exists_still_works(self):
        """
        Make sure IF NOT EXISTS is preserved when operator_class is set.
        """
        idx = CreateIndex(
            ItemTable,
            [ItemTable.name],
            method=IndexMethod.btree,
            if_not_exists=True,
            operator_class="gin_trgm_ops",
        )
        ddl = idx.postgres_ddl[0]
        self.assertIn("IF NOT EXISTS", ddl)
        self.assertIn("gin_trgm_ops", ddl)


class TestCreateIndexValidation(TestCase):

    def test_schema_qualified_operator_class(self):
        """
        Make sure an operator class can be schema qualified, for when the
        extension is installed in another schema (e.g. on Supabase).
        """
        idx = CreateIndex(
            ItemTable,
            [ItemTable.name],
            method=IndexMethod.gin,
            operator_class="extensions.gin_trgm_ops",
        )
        self.assertIn('"name" extensions.gin_trgm_ops', idx.postgres_ddl[0])

    def test_invalid_operator_class(self):
        """
        Make sure an operator class which isn't an identifier is rejected.
        """
        for operator_class in (
            "gin_trgm_ops); DROP TABLE band; --",
            "gin trgm ops",
            "a.b.c",
            "",
        ):
            with self.subTest(operator_class=operator_class):
                with self.assertRaises(ValueError):
                    CreateIndex(
                        ItemTable,
                        [ItemTable.name],
                        method=IndexMethod.gin,
                        operator_class=operator_class,
                    )

    def test_operator_class_checked_at_ddl_time(self):
        """
        Make sure the operator class is also checked if the attribute is
        changed after the ``CreateIndex`` is created.
        """
        idx = CreateIndex(ItemTable, [ItemTable.name], method=IndexMethod.gin)
        idx.operator_class = "gin_trgm_ops); DROP TABLE band; --"
        with self.assertRaises(ValueError):
            idx.postgres_ddl

    def test_index_param_values(self):
        """
        Make sure bools, ints, floats, and keywords are rendered correctly.
        """
        idx = CreateIndex(
            ItemTable,
            [ItemTable.name],
            method=IndexMethod.gist,
            index_params={
                "fastupdate": False,
                "m": 16,
                "fillfactor": 90.5,
                "buffering": "auto",
            },
        )
        self.assertIn(
            "WITH (fastupdate=false, m=16, fillfactor=90.5, buffering=auto)",
            idx.postgres_ddl[0],
        )

    def test_invalid_index_params(self):
        """
        Make sure invalid keys and values are rejected.
        """
        for index_params in (
            {"m": "16); DROP TABLE band; --"},
            {"m); DROP TABLE band; --": 16},
            {"m": None},
            {"m": [16]},
        ):
            with self.subTest(index_params=index_params):
                with self.assertRaises(ValueError):
                    CreateIndex(
                        ItemTable,
                        [ItemTable.name],
                        method=IndexMethod.hnsw,
                        index_params=index_params,
                    )


@sqlite_only
class TestCreateIndexSQLite(TestCase):

    def test_operator_class_raises(self):
        """
        SQLite doesn't support operator classes, so raise an error instead
        of silently ignoring it.
        """
        idx = CreateIndex(
            ItemTable,
            [ItemTable.name],
            operator_class="text_pattern_ops",
        )
        with self.assertRaises(ValueError):
            idx.sqlite_ddl

    def test_index_params_raises(self):
        """
        SQLite doesn't support index params, so raise an error instead of
        silently ignoring them.
        """
        idx = CreateIndex(
            ItemTable,
            [ItemTable.name],
            index_params={"fillfactor": 90},
        )
        with self.assertRaises(ValueError):
            idx.sqlite_ddl
