from tests.base import DBTestCase, engines_only, sqlite_only
from tests.example_apps.music.tables import Band, Manager


class TestGetAll(DBTestCase):
    def test_get_all(self):
        self.insert_row()

        response = Band.objects().run_sync()

        self.assertEqual(len(response), 1)

        instance = response[0]

        self.assertIsInstance(instance, Band)
        self.assertEqual(instance.name, "Pythonistas")

        # Now try changing the value and saving it.
        instance.name = "Rustaceans"
        save_query = instance.save()
        save_query.run_sync()

        self.assertEqual(
            Band.select(Band.name).output(as_list=True).run_sync()[0],
            "Rustaceans",
        )


class TestOffset(DBTestCase):
    @engines_only("postgres", "cockroach")
    def test_offset_postgres(self):
        """
        Postgres can do an offset without a limit clause.
        """
        self.insert_rows()
        response = Band.objects().order_by(Band.name).offset(1).run_sync()
        self.assertEqual(
            [i.name for i in response], ["Pythonistas", "Rustaceans"]
        )

    @sqlite_only
    def test_offset_sqlite(self):
        """
        SQLite requires a limit clause for offset to work.
        """
        self.insert_rows()
        query = Band.objects().order_by(Band.name).offset(1)

        with self.assertRaises(ValueError):
            query.run_sync()

        query = query.limit(5)

        response = query.run_sync()

        self.assertEqual(
            [i.name for i in response], ["Pythonistas", "Rustaceans"]
        )


class TestGet(DBTestCase):
    def test_get(self):
        self.insert_row()

        band = Band.objects().get(Band.name == "Pythonistas").run_sync()

        self.assertEqual(band.name, "Pythonistas")

    def test_get_prefetch(self):
        self.insert_rows()

        # With prefetch clause
        band = (
            Band.objects()
            .get((Band.name == "Pythonistas"))
            .prefetch(Band.manager)
            .run_sync()
        )
        self.assertIsInstance(band.manager, Manager)

        # Just passing it straight into objects
        band = (
            Band.objects(Band.manager)
            .get((Band.name == "Pythonistas"))
            .run_sync()
        )
        self.assertIsInstance(band.manager, Manager)


class TestGetOrCreate(DBTestCase):
    def test_simple_where_clause(self):
        """
        Make sure `get_or_create` works for simple where clauses.
        """
        # When the row doesn't exist in the db:
        Band.objects().get_or_create(
            Band.name == "Pink Floyd", defaults={"popularity": 100}
        ).run_sync()

        instance = (
            Band.objects().where(Band.name == "Pink Floyd").first().run_sync()
        )

        self.assertIsInstance(instance, Band)
        self.assertEqual(instance.name, "Pink Floyd")
        self.assertEqual(instance.popularity, 100)

        # When the row already exists in the db:
        Band.objects().get_or_create(
            Band.name == "Pink Floyd", defaults={Band.popularity: 100}
        ).run_sync()

        instance = (
            Band.objects().where(Band.name == "Pink Floyd").first().run_sync()
        )

        self.assertIsInstance(instance, Band)
        self.assertEqual(instance.name, "Pink Floyd")
        self.assertEqual(instance.popularity, 100)

    def test_complex_where_clause(self):
        """
        Make sure `get_or_create` works with complex where clauses.
        """
        self.insert_rows()

        # When the row already exists in the db:
        instance = (
            Band.objects()
            .get_or_create(
                (Band.name == "Pythonistas") & (Band.popularity == 1000)
            )
            .run_sync()
        )
        self.assertIsInstance(instance, Band)
        self.assertEqual(instance._was_created, False)

        # When the row doesn't exist in the db:
        instance = (
            Band.objects()
            .get_or_create(
                (Band.name == "Pythonistas2") & (Band.popularity == 2000)
            )
            .run_sync()
        )
        self.assertIsInstance(instance, Band)
        self.assertEqual(instance._was_created, True)

    def test_very_complex_where_clause(self):
        """
        Make sure `get_or_create` works with very complex where clauses.
        """
        self.insert_rows()

        # When the row already exists in the db:
        instance = (
            Band.objects()
            .get_or_create(
                (Band.name == "Pythonistas")
                & (Band.popularity > 0)
                & (Band.popularity < 5000)
            )
            .run_sync()
        )
        self.assertIsInstance(instance, Band)
        self.assertEqual(instance._was_created, False)

        # When the row doesn't exist in the db:
        instance = (
            Band.objects()
            .get_or_create(
                (Band.name == "Pythonistas2")
                & (Band.popularity > 10)
                & (Band.popularity < 5000)
            )
            .run_sync()
        )
        self.assertIsInstance(instance, Band)
        self.assertEqual(instance._was_created, True)

        # The values in the > and < should be ignored, and the default should
        # be used for the column.
        self.assertEqual(instance.popularity, 0)

    def test_joins(self):
        """
        Make sure that that `get_or_create` creates rows correctly when using
        joins.
        """
        instance = (
            Band.objects()
            .get_or_create(
                (Band.name == "My new band")
                & (Band.manager.name == "Excellent manager")
            )
            .run_sync()
        )
        self.assertIsInstance(instance, Band)
        self.assertEqual(instance._was_created, True)

        # We want to make sure the band name isn't 'Excellent manager' by
        # mistake.
        self.assertEqual(Band.name, "My new band")

    def test_prefetch_existing_object(self):
        """
        Make sure that that `get_or_create` works with the `prefetch` clause,
        when it's an existing row in the database.
        """
        self.insert_rows()

        # With prefetch clause
        band = (
            Band.objects()
            .get_or_create((Band.name == "Pythonistas"))
            .prefetch(Band.manager)
            .run_sync()
        )
        self.assertIsInstance(band.manager, Manager)
        self.assertEqual(band.manager.name, "Guido")

        # Just passing it straight into objects
        band = (
            Band.objects(Band.manager)
            .get_or_create((Band.name == "Pythonistas"))
            .run_sync()
        )
        self.assertIsInstance(band.manager, Manager)
        self.assertEqual(band.manager.name, "Guido")

    def test_prefetch_new_object(self):
        """
        Make sure that that `get_or_create` works with the `prefetch` clause,
        when the row is being created in the database.
        """
        manager = Manager({Manager.name: "Guido"})
        manager.save().run_sync()

        # With prefetch clause
        band = (
            Band.objects()
            .get_or_create(
                (Band.name == "New Band") & (Band.manager == manager)
            )
            .prefetch(Band.manager)
            .run_sync()
        )
        self.assertIsInstance(band.manager, Manager)
        self.assertEqual(band.name, "New Band")

        # Just passing it straight into objects
        band = (
            Band.objects(Band.manager)
            .get_or_create(
                (Band.name == "New Band 2") & (Band.manager == manager)
            )
            .run_sync()
        )
        self.assertIsInstance(band.manager, Manager)
        self.assertEqual(band.name, "New Band 2")
        self.assertEqual(band.manager.name, "Guido")
