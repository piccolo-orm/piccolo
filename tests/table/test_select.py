from unittest import TestCase

from piccolo.apps.user.tables import BaseUser
from piccolo.columns.combination import WhereRaw
from piccolo.query.methods.select import Avg, Count, Max, Min, Sum
from tests.base import DBTestCase, postgres_only, sqlite_only
from tests.example_apps.music.tables import Band, Concert, Manager, Venue


class TestSelect(DBTestCase):
    def test_query_all_columns(self):
        self.insert_row()

        response = Band.select().run_sync()

        self.assertDictEqual(
            response[0],
            {"id": 1, "name": "Pythonistas", "manager": 1, "popularity": 1000},
        )

    def test_query_some_columns(self):
        self.insert_row()

        response = Band.select(Band.name).run_sync()

        self.assertDictEqual(response[0], {"name": "Pythonistas"})

    def test_where_equals(self):
        self.insert_row()

        manager = Manager.objects().first().run_sync()

        # This is the recommended way of running these types of queries:
        response = (
            Band.select(Band.name)
            .where(
                Band.manager.id
                == getattr(manager, Band._meta.primary_key._meta.name)
            )
            .run_sync()
        )
        self.assertEqual(response, [{"name": "Pythonistas"}])

        # Other cases which should work:
        response = (
            Band.select(Band.name)
            .where(
                Band.manager
                == getattr(manager, Manager._meta.primary_key._meta.name)
            )
            .run_sync()
        )
        self.assertEqual(response, [{"name": "Pythonistas"}])

        response = (
            Band.select(Band.name)
            .where(
                Band.manager.id
                == getattr(manager, Manager._meta.primary_key._meta.name)
            )
            .run_sync()
        )
        self.assertEqual(response, [{"name": "Pythonistas"}])

        # check multiple arguments inside WHERE clause
        response = (
            Band.select(Band.name)
            .where(Band.manager.id == 1, Band.popularity == 500)
            .run_sync()
        )
        self.assertEqual(response, [])

        # check empty WHERE clause
        response = Band.select(Band.name).where().run_sync()
        self.assertEqual(response, [{"name": "Pythonistas"}])

    @postgres_only
    def test_where_like_postgres(self):
        """
        Postgres' LIKE is case sensitive.
        """
        self.insert_rows()

        for like_query in ("Python%", "Pythonistas", "%istas", "%ist%"):
            response = (
                Band.select(Band.name)
                .where(Band.name.like(like_query))
                .run_sync()
            )

            self.assertEqual(response, [{"name": "Pythonistas"}])

        for like_query in (
            "PyThonISTAs",
            "PYth%",
            "%ISTAS",
            "%Ist%",
            "PYTHONISTAS",
        ):
            response = (
                Band.select(Band.name)
                .where(Band.name.like(like_query))
                .run_sync()
            )

            self.assertEqual(response, [])

    @sqlite_only
    def test_where_like_sqlite(self):
        """
        SQLite's LIKE is case insensitive for ASCII characters,
        i.e. a == 'A' -> True.
        """
        self.insert_rows()

        for like_query in (
            "Python%",
            "Pythonistas",
            "%istas",
            "%ist%",
            "PYTHONISTAS",
        ):
            response = (
                Band.select(Band.name)
                .where(Band.name.like(like_query))
                .run_sync()
            )

            self.assertEqual(response, [{"name": "Pythonistas"}])

        for like_query in (
            "xyz",
            "XYZ%",
            "%xyz",
            "%xyz%",
        ):
            response = (
                Band.select(Band.name)
                .where(Band.name.like(like_query))
                .run_sync()
            )

            self.assertEqual(response, [])

    @sqlite_only
    def test_where_ilike_sqlite(self):
        """
        SQLite doesn't support ILIKE, so it's just a proxy to LIKE. We still
        have a test to make sure it proxies correctly.
        """
        self.insert_rows()

        for ilike_query in (
            "Python%",
            "Pythonistas",
            "pythonistas",
            "PytHonIStas",
            "%istas",
            "%ist%",
            "%IST%",
        ):
            self.assertEqual(
                Band.select(Band.name)
                .where(Band.name.ilike(ilike_query))
                .run_sync(),
                Band.select(Band.name)
                .where(Band.name.like(ilike_query))
                .run_sync(),
            )

    @postgres_only
    def test_where_ilike_postgres(self):
        """
        Only Postgres has ILIKE - it's not in the SQL standard. It's for
        case insensitive matching, i.e. 'Foo' == 'foo' -> True.
        """
        self.insert_rows()

        for ilike_query in (
            "Python%",
            "Pythonistas",
            "pythonistas",
            "PytHonIStas",
            "%istas",
            "%ist%",
            "%IST%",
        ):
            response = (
                Band.select(Band.name)
                .where(Band.name.ilike(ilike_query))
                .run_sync()
            )

            self.assertEqual(response, [{"name": "Pythonistas"}])

        for ilike_query in ("Pythonistas1", "%123", "%xyz%"):
            response = (
                Band.select(Band.name)
                .where(Band.name.ilike(ilike_query))
                .run_sync()
            )

            self.assertEqual(response, [])

    def test_where_not_like(self):
        self.insert_rows()

        response = (
            Band.select(Band.name)
            .where(Band.name.not_like("Python%"))
            .order_by(Band.name)
            .run_sync()
        )

        self.assertEqual(
            response, [{"name": "CSharps"}, {"name": "Rustaceans"}]
        )

    def test_where_greater_than(self):
        self.insert_rows()

        response = (
            Band.select(Band.name).where(Band.popularity > 1000).run_sync()
        )

        self.assertEqual(response, [{"name": "Rustaceans"}])

    def test_where_is_null(self):
        self.insert_rows()

        Band(name="Managerless", popularity=0, manager=None).save().run_sync()

        queries = (
            Band.select(Band.name).where(Band.manager == None),  # noqa
            Band.select(Band.name).where(Band.manager.is_null()),
        )

        for query in queries:
            response = query.run_sync()
            self.assertEqual(response, [{"name": "Managerless"}])

    def test_where_is_not_null(self):
        self.insert_rows()

        Band(name="Managerless", popularity=0, manager=None).save().run_sync()

        queries = (
            Band.select(Band.name).where(Band.manager != None),  # noqa
            Band.select(Band.name).where(Band.manager.is_not_null()),
        )

        for query in queries:
            response = query.run_sync()
            self.assertEqual(
                response,
                [
                    {"name": "Pythonistas"},
                    {"name": "Rustaceans"},
                    {"name": "CSharps"},
                ],
            )

    def test_where_greater_equal_than(self):
        self.insert_rows()

        response = (
            Band.select(Band.name)
            .where(Band.popularity >= 1000)
            .order_by(Band.name)
            .run_sync()
        )

        self.assertEqual(
            response, [{"name": "Pythonistas"}, {"name": "Rustaceans"}]
        )

    def test_where_less_than(self):
        self.insert_rows()

        response = (
            Band.select(Band.name).where(Band.popularity < 1000).run_sync()
        )

        self.assertEqual(response, [{"name": "CSharps"}])

    def test_where_less_equal_than(self):
        self.insert_rows()

        response = (
            Band.select(Band.name).where(Band.popularity <= 1000).run_sync()
        )

        self.assertEqual(
            response, [{"name": "Pythonistas"}, {"name": "CSharps"}]
        )

    def test_where_raw(self):
        """
        Make sure raw SQL passed in to a where clause works as expected.
        """
        self.insert_rows()

        response = (
            Band.select(Band.name)
            .where(WhereRaw("name = 'Pythonistas'"))
            .run_sync()
        )

        self.assertEqual(response, [{"name": "Pythonistas"}])

    def test_where_raw_with_args(self):
        """
        Make sure raw SQL with args, passed in to a where clause, works
        as expected.
        """
        self.insert_rows()

        response = (
            Band.select(Band.name)
            .where(WhereRaw("name = {}", "Pythonistas"))
            .run_sync()
        )

        self.assertEqual(response, [{"name": "Pythonistas"}])

    def test_where_raw_combined_with_where(self):
        """
        Make sure WhereRaw can be combined with Where.
        """
        self.insert_rows()

        response = (
            Band.select(Band.name)
            .where(
                WhereRaw("name = 'Pythonistas'") | (Band.name == "Rustaceans")
            )
            .run_sync()
        )

        self.assertEqual(
            response, [{"name": "Pythonistas"}, {"name": "Rustaceans"}]
        )

    def test_where_and(self):
        self.insert_rows()

        response = (
            Band.select(Band.name)
            .where((Band.popularity <= 1000) & (Band.name.like("Python%")))
            .run_sync()
        )

        self.assertEqual(response, [{"name": "Pythonistas"}])

    def test_where_or(self):
        self.insert_rows()

        response = (
            Band.select(Band.name)
            .where((Band.name == "Rustaceans") | (Band.name == "CSharps"))
            .order_by(Band.name)
            .run_sync()
        )

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

        self.assertEqual(
            response, [{"name": "CSharps"}, {"name": "Rustaceans"}]
        )

    def test_limit(self):
        self.insert_rows()

        response = (
            Band.select(Band.name).order_by(Band.name).limit(1).run_sync()
        )

        self.assertEqual(response, [{"name": "CSharps"}])

    @postgres_only
    def test_offset_postgres(self):
        self.insert_rows()

        response = (
            Band.select(Band.name).order_by(Band.name).offset(1).run_sync()
        )

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

        self.assertEqual(
            response, [{"name": "Pythonistas"}, {"name": "Rustaceans"}]
        )

    def test_first(self):
        self.insert_rows()

        response = (
            Band.select(Band.name).order_by(Band.name).first().run_sync()
        )

        self.assertEqual(response, {"name": "CSharps"})

    def test_order_by_ascending(self):
        self.insert_rows()

        response = (
            Band.select(Band.name).order_by(Band.name).limit(1).run_sync()
        )

        self.assertEqual(response, [{"name": "CSharps"}])

    def test_order_by_decending(self):
        self.insert_rows()

        response = (
            Band.select(Band.name)
            .order_by(Band.name, ascending=False)
            .limit(1)
            .run_sync()
        )

        self.assertEqual(response, [{"name": "Rustaceans"}])

    def test_count(self):
        self.insert_rows()

        response = Band.count().where(Band.name == "Pythonistas").run_sync()

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

    def test_count_with_alias_group_by(self):
        """
        Test grouping and counting all rows with alias.
        """
        self.insert_rows()
        self.insert_rows()

        response = (
            Band.select(Band.name, Count(alias="total"))
            .group_by(Band.name)
            .order_by(Band.name)
            .run_sync()
        )

        self.assertTrue(
            response
            == [
                {"name": "CSharps", "total": 2},
                {"name": "Pythonistas", "total": 2},
                {"name": "Rustaceans", "total": 2},
            ]
        )

    def test_count_with_as_alias_group_by(self):
        """
        Test grouping and counting all rows with as_alias.
        """
        self.insert_rows()
        self.insert_rows()

        response = (
            Band.select(Band.name, Count().as_alias("total"))
            .group_by(Band.name)
            .order_by(Band.name)
            .run_sync()
        )

        self.assertTrue(
            response
            == [
                {"name": "CSharps", "total": 2},
                {"name": "Pythonistas", "total": 2},
                {"name": "Rustaceans", "total": 2},
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

    def test_avg(self):
        self.insert_rows()

        response = Band.select(Avg(Band.popularity)).first().run_sync()

        self.assertTrue(float(response["avg"]) == 1003.3333333333334)

    def test_avg_alias(self):
        self.insert_rows()

        response = (
            Band.select(Avg(Band.popularity, alias="popularity_avg"))
            .first()
            .run_sync()
        )

        self.assertTrue(
            float(response["popularity_avg"]) == 1003.3333333333334
        )

    def test_avg_as_alias_method(self):
        self.insert_rows()

        response = (
            Band.select(Avg(Band.popularity).as_alias("popularity_avg"))
            .first()
            .run_sync()
        )

        self.assertTrue(
            float(response["popularity_avg"]) == 1003.3333333333334
        )

    def test_avg_with_where_clause(self):
        self.insert_rows()

        response = (
            Band.select(Avg(Band.popularity))
            .where(Band.popularity > 500)
            .first()
            .run_sync()
        )

        self.assertTrue(response["avg"] == 1500)

    def test_avg_alias_with_where_clause(self):
        """
        Make sure we can specify aliases for the aggregate function,
        when the column is also being used in a where clause.
        """
        self.insert_rows()

        response = (
            Band.select(Avg(Band.popularity, alias="popularity_avg"))
            .where(Band.popularity > 500)
            .first()
            .run_sync()
        )

        self.assertTrue(response["popularity_avg"] == 1500)

    def test_avg_as_alias_method_with_where_clause(self):
        """
        Make sure we can specify as_alias method for the aggregate function,
        when the column is also being used in a where clause.
        """
        self.insert_rows()

        response = (
            Band.select(Avg(Band.popularity).as_alias("popularity_avg"))
            .where(Band.popularity > 500)
            .first()
            .run_sync()
        )

        self.assertTrue(response["popularity_avg"] == 1500)

    def test_max(self):
        self.insert_rows()

        response = Band.select(Max(Band.popularity)).first().run_sync()

        self.assertTrue(response["max"] == 2000)

    def test_max_alias(self):
        self.insert_rows()

        response = (
            Band.select(Max(Band.popularity, alias="popularity_max"))
            .first()
            .run_sync()
        )

        self.assertTrue(response["popularity_max"] == 2000)

    def test_max_as_alias_method(self):
        self.insert_rows()

        response = (
            Band.select(Max(Band.popularity).as_alias("popularity_max"))
            .first()
            .run_sync()
        )

        self.assertTrue(response["popularity_max"] == 2000)

    def test_min(self):
        self.insert_rows()

        response = Band.select(Min(Band.popularity)).first().run_sync()

        self.assertTrue(response["min"] == 10)

    def test_min_alias(self):
        self.insert_rows()

        response = (
            Band.select(Min(Band.popularity, alias="popularity_min"))
            .first()
            .run_sync()
        )

        self.assertTrue(response["popularity_min"] == 10)

    def test_min_as_alias_method(self):
        self.insert_rows()

        response = (
            Band.select(Min(Band.popularity).as_alias("popularity_min"))
            .first()
            .run_sync()
        )

        self.assertTrue(response["popularity_min"] == 10)

    def test_sum(self):
        self.insert_rows()

        response = Band.select(Sum(Band.popularity)).first().run_sync()

        self.assertTrue(response["sum"] == 3010)

    def test_sum_alias(self):
        self.insert_rows()

        response = (
            Band.select(Sum(Band.popularity, alias="popularity_sum"))
            .first()
            .run_sync()
        )

        self.assertTrue(response["popularity_sum"] == 3010)

    def test_sum_as_alias_method(self):
        self.insert_rows()

        response = (
            Band.select(Sum(Band.popularity).as_alias("popularity_sum"))
            .first()
            .run_sync()
        )

        self.assertTrue(response["popularity_sum"] == 3010)

    def test_sum_with_where_clause(self):
        self.insert_rows()

        response = (
            Band.select(Sum(Band.popularity))
            .where(Band.popularity > 500)
            .first()
            .run_sync()
        )

        self.assertTrue(response["sum"] == 3000)

    def test_sum_alias_with_where_clause(self):
        """
        Make sure we can specify aliases for the aggregate function,
        when the column is also being used in a where clause.
        """
        self.insert_rows()

        response = (
            Band.select(Sum(Band.popularity, alias="popularity_sum"))
            .where(Band.popularity > 500)
            .first()
            .run_sync()
        )

        self.assertTrue(response["popularity_sum"] == 3000)

    def test_sum_as_alias_method_with_where_clause(self):
        """
        Make sure we can specify as_alias method for the aggregate function,
        when the column is also being used in a where clause.
        """
        self.insert_rows()

        response = (
            Band.select(Sum(Band.popularity).as_alias("popularity_sum"))
            .where(Band.popularity > 500)
            .first()
            .run_sync()
        )

        self.assertTrue(response["popularity_sum"] == 3000)

    def test_chain_different_functions(self):
        self.insert_rows()

        response = (
            Band.select(Avg(Band.popularity), Sum(Band.popularity))
            .first()
            .run_sync()
        )

        self.assertTrue(float(response["avg"]) == 1003.3333333333334)
        self.assertTrue(response["sum"] == 3010)

    def test_chain_different_functions_alias(self):
        self.insert_rows()

        response = (
            Band.select(
                Avg(Band.popularity, alias="popularity_avg"),
                Sum(Band.popularity, alias="popularity_sum"),
            )
            .first()
            .run_sync()
        )

        self.assertTrue(
            float(response["popularity_avg"]) == 1003.3333333333334
        )
        self.assertTrue(response["popularity_sum"] == 3010)

    def test_avg_validation(self):
        with self.assertRaises(ValueError):
            Band.select(Avg(Band.name)).run_sync()

    def test_sum_validation(self):
        with self.assertRaises(ValueError):
            Band.select(Sum(Band.name)).run_sync()

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
            .columns(Band._meta.primary_key)
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


class TestSelectSecretParameter(TestCase):
    def setUp(self):
        Venue.create_table().run_sync()

    def tearDown(self):
        Venue.alter().drop_table().run_sync()

    def test_secret_parameter(self):
        """
        Make sure that fields with parameter ``secret=True`` are omitted
        from the response when requested.
        """
        venue = Venue(name="The Garage", capacity=1000)
        venue.save().run_sync()

        venue_dict = Venue.select(exclude_secrets=True).first().run_sync()
        self.assertTrue(venue_dict, {"id": 1, "name": "The Garage"})
        self.assertTrue("capacity" not in venue_dict.keys())
