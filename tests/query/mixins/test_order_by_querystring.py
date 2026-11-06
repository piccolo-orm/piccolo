from unittest import TestCase

from piccolo.columns.column_types import Vector
from piccolo.query.mixins import OrderBy, OrderByItem, OrderByRaw
from piccolo.querystring import QueryString
from piccolo.table import Table
from piccolo.testing.test_case import TableTest
from tests.base import postgres_only
from tests.example_apps.music.tables import Band, Manager


class ItemTable(Table):
    embedding = Vector(dimensions=3)


@postgres_only
class TestOrderByQueryString(TestCase):

    def test_querystring_in_order_by_item(self):
        """
        Make sure a QueryString can be used as an order_by column, producing
        the correct ASC SQL.
        """
        qs = ItemTable.embedding.cosine_distance([0.1, 0.2, 0.3])
        item = OrderByItem(columns=[qs], ascending=True)
        ob = OrderBy(order_by_items=[item])
        sql = str(ob.querystring)
        self.assertIn("ORDER BY", sql)
        self.assertIn("<=>", sql)
        self.assertIn("ASC", sql)

    def test_querystring_descending(self):
        """
        Make sure ascending=False produces DESC when ordering by a
        QueryString.
        """
        qs = ItemTable.embedding.l2_distance([0.1, 0.2, 0.3])
        item = OrderByItem(columns=[qs], ascending=False)
        ob = OrderBy(order_by_items=[item])
        sql = str(ob.querystring)
        self.assertIn("DESC", sql)

    def test_raw_querystring_in_order_by(self):
        """
        Make sure a plain QueryString (not a column distance method) can
        be used in order_by.
        """
        qs = QueryString("random()")
        item = OrderByItem(columns=[qs], ascending=True)
        ob = OrderBy(order_by_items=[item])
        sql = str(ob.querystring)
        self.assertIn("random()", sql)
        self.assertIn("ASC", sql)

    def test_mixed_column_and_querystring(self):
        """
        Make sure ordering by both a Column and a QueryString in one query
        produces both expressions in the ORDER BY clause.
        """
        qs = ItemTable.embedding.cosine_distance([0.1, 0.2, 0.3])
        raw = OrderByRaw("random()")
        item1 = OrderByItem(columns=[qs], ascending=True)
        item2 = OrderByItem(columns=[raw], ascending=False)
        ob = OrderBy(order_by_items=[item1, item2])
        sql = str(ob.querystring)
        self.assertIn("<=>", sql)
        self.assertIn("random()", sql)


class TestOrderByQueryStringJoins(TestCase):

    def test_join_added_for_querystring_column(self):
        """
        Make sure that if a QueryString in order_by references a column on a
        related table, the join is added.
        """
        query = Band.select(Band.name).order_by(
            QueryString("{}", Band.manager.name)
        )
        sql = str(query)
        self.assertIn('LEFT JOIN "manager" "band$manager"', sql)
        self.assertIn('ORDER BY "band$manager"."name" ASC', sql)


class TestOrderByQueryStringJoinsRun(TableTest):
    tables = [Manager, Band]

    def test_query_runs(self):
        """
        Make sure the query with a join from order_by actually runs, and
        orders by the related column.
        """
        guido = Manager({Manager.name: "Guido"})
        graydon = Manager({Manager.name: "Graydon"})
        Manager.insert(guido, graydon).run_sync()
        Band.insert(
            Band({Band.name: "Pythonistas", Band.manager: guido}),
            Band({Band.name: "Rustaceans", Band.manager: graydon}),
        ).run_sync()

        response = (
            Band.select(Band.name)
            .order_by(QueryString("{}", Band.manager.name), ascending=False)
            .run_sync()
        )
        self.assertListEqual(
            response, [{"name": "Pythonistas"}, {"name": "Rustaceans"}]
        )
