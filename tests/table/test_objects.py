from ..base import DBTestCase, postgres_only, sqlite_only
from ..example_app.tables import Band


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

        print(f"response = {response}")

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

        print(f"response = {response}")

        self.assertEqual(
            [i.name for i in response], ["Pythonistas", "Rustaceans"]
        )

    def test_get_or_create(self):
        Band.objects().get_or_create(
            Band.name == "Pink Floyd", defaults={"popularity": 100}
        ).run_sync()

        instance = (
            Band.objects().where(Band.name == "Pink Floyd").first().run_sync()
        )

        self.assertTrue(isinstance(instance, Band))
        self.assertTrue(instance.name == "Pink Floyd")
        self.assertTrue(instance.popularity == 100)

        Band.objects().get_or_create(
            Band.name == "Pink Floyd", defaults={Band.popularity: 100}
        ).run_sync()

        instance = (
            Band.objects().where(Band.name == "Pink Floyd").first().run_sync()
        )

        self.assertTrue(isinstance(instance, Band))
        self.assertTrue(instance.name == "Pink Floyd")
        self.assertTrue(instance.popularity == 100)
