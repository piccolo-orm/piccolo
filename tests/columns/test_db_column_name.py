from piccolo.columns.column_types import Integer, Varchar
from piccolo.table import Table
from tests.base import DBTestCase, postgres_only


class Band(Table):
    name = Varchar(db_column_name="regrettable_column_name")
    popularity = Integer()


class TestDBColumnName(DBTestCase):
    """
    By using the ``db_column_name`` arg, the user can map a ``Column`` to a
    database column with the given name.
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
        band = Band(name="Pythonistas", popularity=1000)
        band.save().run_sync()

        band_from_db = Band.objects().first().run_sync()
        self.assertTrue(band_from_db.name == "Pythonistas")

    def test_create(self):
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
        database.
        """
        Band.objects().create(name="Pythonistas", popularity=1000).run_sync()

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
