from unittest import TestCase

from piccolo.columns.column_types import (
    Text,
    Tsquery,
    Tsvector,
    Varchar,
    Vector,
)
from piccolo.columns.indexes import IndexMethod
from piccolo.query.functions.text_search import ToTsquery
from piccolo.query.methods.create_index import CreateIndex
from piccolo.querystring import QueryString
from piccolo.table import Table
from piccolo.testing.test_case import TableTest
from tests.base import (
    engines_only,
    pg_trgm_installed,
    pgvector_installed,
    postgres_only,
)


class ItemTable(Table):
    embedding = Vector(dimensions=3)


class ArticleTable(Table):
    search_vector = Tsvector(null=True)
    title = Varchar()
    body = Text()


class QueryTable(Table):
    tsq = Tsquery()


@engines_only("sqlite", "cockroach")
class TestVectorNonPostgres(TestCase):

    def test_column_type_raises(self):
        """
        Vector is only supported on PostgreSQL — should raise
        NotImplementedError on SQLite and CockroachDB.
        """
        with self.assertRaises(NotImplementedError):
            _ = ItemTable.embedding.column_type


@postgres_only
class TestVector(TestCase):

    def test_dimensions_in_params(self):
        """
        The dimensions param must be stored in _meta.params for migration
        serialisation.
        """
        col = Vector(dimensions=256)
        self.assertEqual(col._meta.params["dimensions"], 256)

    def test_cosine_distance_sql(self):
        """
        cosine_distance() must return a QueryString using the <=> operator
        with a ::vector cast.
        """
        qs = ItemTable.embedding.cosine_distance([0.1, 0.2, 0.3])
        self.assertIsInstance(qs, QueryString)
        sql = str(qs)
        self.assertIn("<=>", sql)
        self.assertIn("::vector", sql)

    def test_l2_distance_sql(self):
        """
        l2_distance() must return a QueryString using the <-> operator
        with a ::vector cast.
        """
        qs = ItemTable.embedding.l2_distance([0.1, 0.2, 0.3])
        sql = str(qs)
        self.assertIn("<->", sql)
        self.assertIn("::vector", sql)

    def test_max_inner_product_sql(self):
        """
        max_inner_product() must return a QueryString using the <#> operator
        with a ::vector cast.
        """
        qs = ItemTable.embedding.max_inner_product([0.1, 0.2, 0.3])
        sql = str(qs)
        self.assertIn("<#>", sql)
        self.assertIn("::vector", sql)


@engines_only("sqlite", "cockroach")
class TestTsvectorNonPostgres(TestCase):

    def test_column_type_raises(self):
        """
        Tsvector is only supported on PostgreSQL — should raise
        NotImplementedError on SQLite and CockroachDB.
        """
        with self.assertRaises(NotImplementedError):
            _ = ArticleTable.search_vector.column_type


@postgres_only
class TestTsvector(TestCase):

    def test_matches_sql(self):
        """
        matches() must return a Where clause using the @@ operator.
        """
        where = ArticleTable.search_vector.matches(ToTsquery("python"))
        sql = str(where.querystring)
        self.assertIn("@@", sql)


@engines_only("sqlite", "cockroach")
class TestTsqueryNonPostgres(TestCase):

    def test_column_type_raises(self):
        """
        Tsquery is only supported on PostgreSQL — should raise
        NotImplementedError on SQLite and CockroachDB.
        """
        with self.assertRaises(NotImplementedError):
            _ = QueryTable.tsq.column_type


@postgres_only
class TestTrigramMixin(TestCase):

    def test_varchar_has_trigram_methods(self):
        """
        Varchar should have trigram_similar and trigram_distance methods
        via TrigramMixin.
        """
        self.assertTrue(hasattr(ArticleTable.title, "trigram_similar"))
        self.assertTrue(hasattr(ArticleTable.title, "trigram_distance"))

    def test_text_has_trigram_methods(self):
        """
        Text should have trigram_similar and trigram_distance methods
        via TrigramMixin.
        """
        self.assertTrue(hasattr(ArticleTable.body, "trigram_similar"))
        self.assertTrue(hasattr(ArticleTable.body, "trigram_distance"))

    def test_trigram_similar_sql(self):
        """
        trigram_similar() must produce a Where clause using the % operator.
        """
        where = ArticleTable.title.trigram_similar("python")
        sql = str(where.querystring)
        self.assertIn("%", sql)

    def test_trigram_distance_sql(self):
        """
        trigram_distance() must return a QueryString using the <-> operator.
        """
        qs = ArticleTable.title.trigram_distance("python")
        self.assertIsInstance(qs, QueryString)
        sql = str(qs)
        self.assertIn("<->", sql)


@pgvector_installed
@postgres_only
class TestVectorIntegration(TableTest):
    tables = [ItemTable]

    def test_insert_and_select(self):
        ItemTable(embedding=[0.1, 0.2, 0.3]).save().run_sync()
        rows = ItemTable.select().run_sync()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["embedding"], [0.1, 0.2, 0.3])

    def test_order_by_cosine_distance(self):
        ItemTable(embedding=[0.1, 0.2, 0.3]).save().run_sync()
        ItemTable(embedding=[0.4, 0.5, 0.6]).save().run_sync()
        rows = (
            ItemTable.select()
            .order_by(ItemTable.embedding.cosine_distance([0.1, 0.2, 0.3]))
            .run_sync()
        )
        self.assertEqual(len(rows), 2)

    def test_order_by_l2_distance(self):
        ItemTable(embedding=[0.1, 0.2, 0.3]).save().run_sync()
        ItemTable(embedding=[0.9, 0.8, 0.7]).save().run_sync()
        rows = (
            ItemTable.select()
            .order_by(ItemTable.embedding.l2_distance([0.0, 0.0, 0.0]))
            .run_sync()
        )
        self.assertEqual(len(rows), 2)

    def test_create_hnsw_index(self):
        CreateIndex(
            table=ItemTable,
            columns=[ItemTable.embedding],
            method=IndexMethod.hnsw,
            operator_class="vector_cosine_ops",
            index_params={"m": 16, "ef_construction": 64},
        ).run_sync()


@postgres_only
class TestTsvectorIntegration(TableTest):
    tables = [ArticleTable]

    def test_insert_and_select(self):
        ArticleTable(
            search_vector="'python':1 'programming':2",
            title="Python guide",
            body="Learn Python",
        ).save().run_sync()
        rows = ArticleTable.select().run_sync()
        self.assertEqual(len(rows), 1)

    def test_matches(self):
        ArticleTable(
            search_vector="'python':1 'programming':2",
            title="Python guide",
            body="Learn Python",
        ).save().run_sync()
        rows = (
            ArticleTable.select()
            .where(ArticleTable.search_vector.matches(ToTsquery("python")))
            .run_sync()
        )
        self.assertEqual(len(rows), 1)

    def test_no_match(self):
        ArticleTable(
            search_vector="'python':1",
            title="Python guide",
            body="Learn Python",
        ).save().run_sync()
        rows = (
            ArticleTable.select()
            .where(ArticleTable.search_vector.matches(ToTsquery("javascript")))
            .run_sync()
        )
        self.assertEqual(len(rows), 0)


@pg_trgm_installed
@postgres_only
class TestTrigramIntegration(TableTest):
    tables = [ArticleTable]

    def test_trigram_similar_where(self):
        ArticleTable(
            title="Python programming", body="Learn Python"
        ).save().run_sync()
        rows = (
            ArticleTable.select()
            .where(ArticleTable.title.trigram_similar("Python"))
            .run_sync()
        )
        self.assertEqual(len(rows), 1)

    def test_trigram_distance_order_by(self):
        ArticleTable(title="Python programming", body="body").save().run_sync()
        ArticleTable(title="Java development", body="body").save().run_sync()
        rows = (
            ArticleTable.select()
            .order_by(ArticleTable.title.trigram_distance("Python"))
            .run_sync()
        )
        self.assertEqual(len(rows), 2)

    def test_create_trgm_gin_index(self):
        CreateIndex(
            table=ArticleTable,
            columns=[ArticleTable.title],
            method=IndexMethod.gin,
            operator_class="gin_trgm_ops",
        ).run_sync()
