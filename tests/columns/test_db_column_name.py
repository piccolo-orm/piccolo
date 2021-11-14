from piccolo.columns.column_types import Integer, Varchar
from piccolo.table import Table
from tests.base import DBTestCase, postgres_only


class Band(Table):
    name = Varchar(db_column_name="regrettable_column_name")
    popularity = Integer()


class TestDBColumnName(DBTestCase):
    """
    By using the ``db_column_name`` arg, the user can map a ``Column`` to a
    database column with a different name. For example:

    .. code-block:: python

        class MyTable(Table):
            class_ = Varchar(db_column_name='class')

    """

    def setUp(self):
        Band.create_table().run_sync()

    def tearDown(self):
        Band.alter().drop_table().run_sync()

    @postgres_only
    def test_column_name_correct(self):
        """
        Make sure the column has the correct name in the database.
        """
        self.get_postgres_column_definition(
            tablename="band", column_name="regrettable_column_name"
        )

        with self.assertRaises(ValueError):
            self.get_postgres_column_definition(
                tablename="band", column_name="name"
            )

    def test_save(self):
        """
        Make sure save queries work correctly.
        """
        band = Band(name="Pythonistas", popularity=1000)
        band.save().run_sync()

        band_from_db = Band.objects().first().run_sync()
        self.assertTrue(band_from_db.name == "Pythonistas")

    def test_create(self):
        """
        Make sure create queries work correctly.
        """
        band = (
            Band.objects()
            .create(name="Pythonistas", popularity=1000)
            .run_sync()
        )
        self.assertTrue(band.name == "Pythonistas")

        band_from_db = Band.objects().first().run_sync()
        self.assertTrue(band_from_db.name == "Pythonistas")

    def test_select(self):
        """
        Make sure that select queries just return what is stored in the
        database. We might add an option in the future which maps the column
        name to it's alias, but it's hard to predict what behaviour the user
        wants.
        """
        Band.objects().create(name="Pythonistas", popularity=1000).run_sync()

        # Make sure we can select all columns
        bands = Band.select().run_sync()
        self.assertEqual(
            bands,
            [
                {
                    "id": 1,
                    "regrettable_column_name": "Pythonistas",
                    "popularity": 1000,
                }
            ],
        )

        # Make sure we can select a single column
        bands = Band.select(Band.name).run_sync()
        self.assertEqual(
            bands,
            [
                {
                    "regrettable_column_name": "Pythonistas",
                }
            ],
        )

        # Make sure aliases still work
        bands = Band.select(Band.name.as_alias("name")).run_sync()
        self.assertEqual(
            bands,
            [
                {
                    "name": "Pythonistas",
                }
            ],
        )

    def test_update(self):
        """
        Make sure update queries work correctly.
        """
        Band.objects().create(name="Pythonistas", popularity=1000).run_sync()

        Band.update({Band.name: "Pythonistas 2"}).run_sync()

        bands = Band.select().run_sync()
        self.assertEqual(
            bands,
            [
                {
                    "id": 1,
                    "regrettable_column_name": "Pythonistas 2",
                    "popularity": 1000,
                }
            ],
        )

        Band.update({"name": "Pythonistas 3"}).run_sync()

        bands = Band.select().run_sync()
        self.assertEqual(
            bands,
            [
                {
                    "id": 1,
                    "regrettable_column_name": "Pythonistas 3",
                    "popularity": 1000,
                }
            ],
        )

    def test_delete(self):
        """
        Make sure delete queries work correctly.
        """
        Band.insert(
            Band(name="Pythonistas", popularity=1000),
            Band(name="Rustaceans", popularity=500),
        ).run_sync()

        bands = Band.select().run_sync()
        self.assertEqual(
            bands,
            [
                {
                    "id": 1,
                    "regrettable_column_name": "Pythonistas",
                    "popularity": 1000,
                },
                {
                    "id": 2,
                    "regrettable_column_name": "Rustaceans",
                    "popularity": 500,
                },
            ],
        )

        Band.delete().where(Band.name == "Rustaceans").run_sync()

        bands = Band.select().run_sync()
        self.assertEqual(
            bands,
            [
                {
                    "id": 1,
                    "regrettable_column_name": "Pythonistas",
                    "popularity": 1000,
                }
            ],
        )
