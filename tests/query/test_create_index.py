from unittest import TestCase

from piccolo.columns.column_types import Varchar, Vector
from piccolo.columns.indexes import IndexMethod
from piccolo.query.methods.create_index import CreateIndex
from piccolo.table import Table
from tests.base import postgres_only


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
