from tests.base import DBTestCase, postgres_only, sqlite_only
from tests.example_apps.music.tables import Band, Manager


class TestObjects(DBTestCase):
    def test_get_all(self):
        self.insert_row()

        response = Band.objects().run_sync()

        self.assertTrue(len(response) == 1)

        instance = response[0]

        self.assertTrue(isinstance(instance, Band))
        self.assertTrue(instance.name == "Pythonistas")

        # Now try changing the value and saving it.
        instance.name = "Rustaceans"
        save_query = instance.save()
        save_query.run_sync()

        self.assertTrue(
            Band.select(Band.name).output(as_list=True).run_sync()[0]
            == "Rustaceans"
        )

    @postgres_only
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

    def test_get(self):
        self.insert_row()

        band = Band.objects().get(Band.name == "Pythonistas").run_sync()

        self.assertTrue(band.name == "Pythonistas")

    def test_get__prefetch(self):
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

    def test_get_or_create(self):
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
        self.assertTrue(instance.name == "Pink Floyd")
        self.assertTrue(instance.popularity == 100)

        # When the row already exists in the db:
        Band.objects().get_or_create(
            Band.name == "Pink Floyd", defaults={Band.popularity: 100}
        ).run_sync()

        instance = (
            Band.objects().where(Band.name == "Pink Floyd").first().run_sync()
        )

        self.assertIsInstance(instance, Band)
        self.assertTrue(instance.name == "Pink Floyd")
        self.assertTrue(instance.popularity == 100)

    def test_get_or_create_complex(self):
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

    def test_get_or_create_very_complex(self):
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

    def test_get_or_create_with_joins(self):
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

    def test_get_or_create__prefetch(self):
        """
        Make sure that that `get_or_create` works with the `prefetch` clause.
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

        # Just passing it straight into objects
        band = (
            Band.objects(Band.manager)
            .get_or_create((Band.name == "Pythonistas"))
            .run_sync()
        )
        self.assertIsInstance(band.manager, Manager)
