from unittest import TestCase

from piccolo.apps.user.tables import BaseUser
from piccolo.query.methods.select import Count

from ..base import DBTestCase, postgres_only, sqlite_only
from ..example_app.tables import Band, Concert


class TestSelect(DBTestCase):
    def test_query_all_columns(self):
        self.insert_row()

        response = Band.select().run_sync()
        print(f"response = {response}")

        self.assertDictEqual(
            response[0],
            {"id": 1, "name": "Pythonistas", "manager": 1, "popularity": 1000},
        )

    def test_query_some_columns(self):
        self.insert_row()

        response = Band.select(Band.name).run_sync()
        print(f"response = {response}")

        self.assertDictEqual(response[0], {"name": "Pythonistas"})

    def test_where_like(self):
        self.insert_rows()

        response = (
            Band.select(Band.name).where(Band.name.like("Python%")).run_sync()
        )

        print(f"response = {response}")

        self.assertEqual(response, [{"name": "Pythonistas"}])

    def test_where_ilike(self):
        self.insert_rows()

        response = (
            Band.select(Band.name).where(Band.name.ilike("python%")).run_sync()
        )

        print(f"response = {response}")

        self.assertEqual(response, [{"name": "Pythonistas"}])

    def test_where_not_like(self):
        self.insert_rows()

        response = (
            Band.select(Band.name)
            .where(Band.name.not_like("Python%"))
            .order_by(Band.name)
            .run_sync()
        )

        print(f"response = {response}")

        self.assertEqual(
            response, [{"name": "CSharps"}, {"name": "Rustaceans"}]
        )

    def test_where_greater_than(self):
        self.insert_rows()

        response = (
            Band.select(Band.name).where(Band.popularity > 1000).run_sync()
        )

        print(f"response = {response}")

        self.assertEqual(response, [{"name": "Rustaceans"}])

    def test_where_greater_equal_than(self):
        self.insert_rows()

        response = (
            Band.select(Band.name)
            .where(Band.popularity >= 1000)
            .order_by(Band.name)
            .run_sync()
        )

        print(f"response = {response}")

        self.assertEqual(
            response, [{"name": "Pythonistas"}, {"name": "Rustaceans"}]
        )

    def test_where_less_than(self):
        self.insert_rows()

        response = (
            Band.select(Band.name).where(Band.popularity < 1000).run_sync()
        )

        print(f"response = {response}")

        self.assertEqual(response, [{"name": "CSharps"}])

    def test_where_less_equal_than(self):
        self.insert_rows()

        response = (
            Band.select(Band.name).where(Band.popularity <= 1000).run_sync()
        )

        print(f"response = {response}")

        self.assertEqual(
            response, [{"name": "Pythonistas"}, {"name": "CSharps"}]
        )

    def test_where_and(self):
        self.insert_rows()

        response = (
            Band.select(Band.name)
            .where((Band.popularity <= 1000) & (Band.name.like("Python%")))
            .run_sync()
        )

        print(f"response = {response}")

        self.assertEqual(response, [{"name": "Pythonistas"}])

    def test_where_or(self):
        self.insert_rows()

        response = (
            Band.select(Band.name)
            .where((Band.name == "Rustaceans") | (Band.name == "CSharps"))
            .order_by(Band.name)
            .run_sync()
        )

        print(f"response = {response}")

        self.assertEqual(
            response, [{"name": "CSharps"}, {"name": "Rustaceans"}]
        )

    def test_multiple_where(self):
        """
        Test that chaining multiple where clauses works results in an AND.
        """
        self.insert_rows()

        query = (
            Band.select(Band.name)
            .where(Band.name == "Rustaceans")
            .where(Band.manager == 2)
        )

        response = query.run_sync()

        print(f"response = {response}")

        self.assertEqual(response, [{"name": "Rustaceans"}])
        self.assertTrue("AND" in query.__str__())

    def test_complex_where(self):
        """
        Test a complex where clause - combining AND, and OR.
        """
        self.insert_rows()

        query = (
            Band.select(Band.name)
            .where(
                ((Band.popularity == 2000) & (Band.manager == 2))
                | ((Band.popularity == 10) & (Band.manager == 3))
            )
            .order_by(Band.name)
        )

        response = query.run_sync()

        print(f"response = {response}")

        self.assertEqual(
            response, [{"name": "CSharps"}, {"name": "Rustaceans"}]
        )

    def test_limit(self):
        self.insert_rows()

        response = (
            Band.select(Band.name).order_by(Band.name).limit(1).run_sync()
        )

        print(f"response = {response}")

        self.assertEqual(response, [{"name": "CSharps"}])

    @postgres_only
    def test_offset_postgres(self):
        self.insert_rows()

        response = (
            Band.select(Band.name).order_by(Band.name).offset(1).run_sync()
        )

        print(f"response = {response}")

        self.assertEqual(
            response, [{"name": "Pythonistas"}, {"name": "Rustaceans"}]
        )

    @sqlite_only
    def test_offset_sqlite(self):
        """
        SQLite requires a limit clause for offset to work.
        """
        self.insert_rows()

        query = Band.select(Band.name).order_by(Band.name).offset(1)

        with self.assertRaises(ValueError):
            query.run_sync()

        query = query.limit(5)
        response = query.run_sync()

        print(f"response = {response}")

        self.assertEqual(
            response, [{"name": "Pythonistas"}, {"name": "Rustaceans"}]
        )

    def test_first(self):
        self.insert_rows()

        response = (
            Band.select(Band.name).order_by(Band.name).first().run_sync()
        )

        print(f"response = {response}")

        self.assertEqual(response, {"name": "CSharps"})

    def test_order_by_ascending(self):
        self.insert_rows()

        response = (
            Band.select(Band.name).order_by(Band.name).limit(1).run_sync()
        )

        print(f"response = {response}")

        self.assertEqual(response, [{"name": "CSharps"}])

    def test_order_by_decending(self):
        self.insert_rows()

        response = (
            Band.select(Band.name)
            .order_by(Band.name, ascending=False)
            .limit(1)
            .run_sync()
        )

        print(f"response = {response}")

        self.assertEqual(response, [{"name": "Rustaceans"}])

    def test_count(self):
        self.insert_rows()

        response = Band.count().where(Band.name == "Pythonistas").run_sync()

        print(f"response = {response}")

        self.assertEqual(response, 1)

    def test_distinct(self):
        """
        Make sure the distinct clause works.
        """
        self.insert_rows()
        self.insert_rows()

        query = Band.select(Band.name).where(Band.name == "Pythonistas")
        self.assertTrue("DISTINCT" not in query.__str__())

        response = query.run_sync()
        self.assertTrue(
            response == [{"name": "Pythonistas"}, {"name": "Pythonistas"}]
        )

        query = query.distinct()
        self.assertTrue("DISTINCT" in query.__str__())

        response = query.run_sync()
        self.assertTrue(response == [{"name": "Pythonistas"}])

    def test_count_group_by(self):
        """
        Test grouping and counting all rows.
        """
        self.insert_rows()
        self.insert_rows()

        response = (
            Band.select(Band.name, Count())
            .group_by(Band.name)
            .order_by(Band.name)
            .run_sync()
        )

        self.assertTrue(
            response
            == [
                {"name": "CSharps", "count": 2},
                {"name": "Pythonistas", "count": 2},
                {"name": "Rustaceans", "count": 2},
            ]
        )

    def test_count_column_group_by(self):
        """
        Test grouping and counting a specific column. Any null values in the
        specified column will be omitted from the count.
        """
        self.insert_rows()
        self.insert_rows()
        self.run_sync(
            """
            INSERT INTO band (
                name,
                manager,
                popularity
            ) VALUES (
                'SomeBand',
                null,
                1000
            );"""
        )

        response = (
            Band.select(Band.manager.name, Count(Band.manager))
            .group_by(Band.manager.name)
            .order_by(Band.manager.name)
            .run_sync()
        )

        # We need to sort them, because SQLite and Postgres treat Null
        # differently when sorting.
        response = sorted(response, key=lambda x: x["manager.name"] or "")

        self.assertTrue(
            response
            == [
                {"manager.name": None, "count": 0},
                {"manager.name": "Graydon", "count": 2},
                {"manager.name": "Guido", "count": 2},
                {"manager.name": "Mads", "count": 2},
            ]
        )

        # This time the nulls should be counted, as we omit the column argument
        # from Count:
        response = (
            Band.select(Band.manager.name, Count())
            .group_by(Band.manager.name)
            .order_by(Band.manager.name)
            .run_sync()
        )

        response = sorted(response, key=lambda x: x["manager.name"] or "")

        self.assertTrue(
            response
            == [
                {"manager.name": None, "count": 1},
                {"manager.name": "Graydon", "count": 2},
                {"manager.name": "Guido", "count": 2},
                {"manager.name": "Mads", "count": 2},
            ]
        )

    def test_columns(self):
        """
        Make sure the colums method can be used to specify which columns to
        query.
        """
        self.insert_rows()

        response = (
            Band.select()
            .columns(Band.name)
            .where(Band.name == "Pythonistas")
            .first()
            .run_sync()
        )
        self.assertTrue(response == {"name": "Pythonistas"})

        # Multiple calls to 'columns' should be additive.
        response = (
            Band.select()
            .columns(Band.id)
            .columns(Band.name)
            .where(Band.name == "Pythonistas")
            .first()
            .run_sync()
        )
        self.assertTrue(response == {"id": 1, "name": "Pythonistas"})

    def test_call_chain(self):
        """
        Make sure the call chain lengths are the correct size.
        """
        self.assertEqual(len(Concert.band_1.name._meta.call_chain), 1)
        self.assertEqual(len(Concert.band_1.manager.name._meta.call_chain), 2)

    def test_as_alias(self):
        """
        Make sure we can specify aliases for the columns.
        """
        self.insert_row()
        response = Band.select(Band.name.as_alias("title")).run_sync()
        self.assertEqual(response, [{"title": "Pythonistas"}])

    def test_as_alias_with_join(self):
        """
        Make sure we can specify aliases for the column, when performing a
        join.
        """
        self.insert_row()
        response = Band.select(
            Band.manager.name.as_alias("manager_name")
        ).run_sync()
        self.assertEqual(response, [{"manager_name": "Guido"}])

    def test_as_alias_with_where_clause(self):
        """
        Make sure we can specify aliases for the column, when the column is
        also being used in a where clause.
        """
        self.insert_row()
        response = (
            Band.select(Band.name, Band.manager.name.as_alias("manager_name"))
            .where(Band.manager.name == "Guido")
            .run_sync()
        )
        self.assertEqual(
            response, [{"name": "Pythonistas", "manager_name": "Guido"}]
        )


class TestSelectSecret(TestCase):
    def setUp(self):
        BaseUser.create_table().run_sync()

    def tearDown(self):
        BaseUser.alter().drop_table().run_sync()

    def test_secret(self):
        """
        Make sure that secret fields are omitted from the response when
        requested.
        """
        user = BaseUser(username="piccolo", password="piccolo123")
        user.save().run_sync()

        user_dict = BaseUser.select(exclude_secrets=True).first().run_sync()
        self.assertTrue("password" not in user_dict.keys())
