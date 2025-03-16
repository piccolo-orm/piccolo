import typing as t

from piccolo.columns.column_types import ForeignKey, Integer, Serial, Varchar
from piccolo.table import Table, create_db_tables_sync, drop_db_tables_sync
from tests.base import DBTestCase, engine_is, engines_only, engines_skip


class Manager(Table):
    id: Serial
    name = Varchar()


class Band(Table):
    id: Serial
    name = Varchar(db_column_name="regrettable_column_name")
    popularity = Integer()
    manager = ForeignKey(Manager, db_column_name="manager_fk")


class TestDBColumnName(DBTestCase):
    """
    By using the ``db_column_name`` arg, the user can map a ``Column`` to a
    database column with a different name. For example:

    .. code-block:: python

        class MyTable(Table):
            class_ = Varchar(db_column_name='class')

    """

    def setUp(self):
        create_db_tables_sync(Band, Manager)

    def tearDown(self):
        drop_db_tables_sync(Band, Manager)

    def insert_band(self, manager: t.Optional[Manager] = None) -> Band:
        band = Band(name="Pythonistas", popularity=1000, manager=manager)
        band.save().run_sync()
        return band

    @engines_only("postgres", "cockroach")
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
        self.insert_band()

        band_from_db = Band.objects().first().run_sync()
        assert band_from_db is not None
        self.assertEqual(band_from_db.name, "Pythonistas")

    def test_create(self):
        """
        Make sure create queries work correctly.
        """
        band = self.insert_band()
        self.assertEqual(band.name, "Pythonistas")

        band_from_db = Band.objects().first().run_sync()
        assert band_from_db is not None
        self.assertEqual(band_from_db.name, "Pythonistas")

    def test_select(self):
        """
        Make sure that select queries just return what is stored in the
        database. We might add an option in the future which maps the column
        name to it's alias, but it's hard to predict what behaviour the user
        wants.
        """
        self.insert_band()

        # Make sure we can select all columns
        bands = Band.select().run_sync()
        if engine_is("cockroach"):
            self.assertEqual(
                bands,
                [
                    {
                        "id": bands[0]["id"],
                        "regrettable_column_name": "Pythonistas",
                        "popularity": 1000,
                        "manager_fk": None,
                    }
                ],
            )
        else:
            self.assertEqual(
                bands,
                [
                    {
                        "id": 1,
                        "regrettable_column_name": "Pythonistas",
                        "popularity": 1000,
                        "manager_fk": None,
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

    def test_join(self):
        """
        Make sure that foreign keys with a ``db_column_name`` specified still
        work for joins.

        https://github.com/piccolo-orm/piccolo/issues/1101

        """
        manager = Manager.objects().create(name="Guido").run_sync()
        band = self.insert_band(manager=manager)

        bands = Band.select().where(Band.manager.name == "Guido").run_sync()

        self.assertListEqual(
            bands,
            [
                {
                    "id": band.id,
                    "manager_fk": manager.id,
                    "popularity": 1000,
                    "regrettable_column_name": "Pythonistas",
                }
            ],
        )

    def test_update(self):
        """
        Make sure update queries work correctly.
        """
        self.insert_band()

        Band.update({Band.name: "Pythonistas 2"}, force=True).run_sync()

        bands = Band.select().run_sync()
        if engine_is("cockroach"):
            self.assertEqual(
                bands,
                [
                    {
                        "id": bands[0]["id"],
                        "regrettable_column_name": "Pythonistas 2",
                        "popularity": 1000,
                        "manager_fk": None,
                    }
                ],
            )
        else:
            self.assertEqual(
                bands,
                [
                    {
                        "id": 1,
                        "regrettable_column_name": "Pythonistas 2",
                        "popularity": 1000,
                        "manager_fk": None,
                    }
                ],
            )

        Band.update({"name": "Pythonistas 3"}, force=True).run_sync()

        bands = Band.select().run_sync()
        if engine_is("cockroach"):
            self.assertEqual(
                bands,
                [
                    {
                        "id": bands[0]["id"],
                        "regrettable_column_name": "Pythonistas 3",
                        "popularity": 1000,
                        "manager_fk": None,
                    }
                ],
            )
        else:
            self.assertEqual(
                bands,
                [
                    {
                        "id": 1,
                        "regrettable_column_name": "Pythonistas 3",
                        "popularity": 1000,
                        "manager_fk": None,
                    }
                ],
            )

    @engines_skip("cockroach")
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
                    "manager_fk": None,
                },
                {
                    "id": 2,
                    "regrettable_column_name": "Rustaceans",
                    "popularity": 500,
                    "manager_fk": None,
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
                    "manager_fk": None,
                }
            ],
        )

    @engines_only("cockroach")
    def test_delete_alt(self):
        """
        Make sure delete queries work correctly.
        """
        result = (
            Band.insert(
                Band(name="Pythonistas", popularity=1000),
                Band(name="Rustaceans", popularity=500),
            )
            .returning(Band.id)
            .run_sync()
        )

        bands = Band.select().run_sync()
        self.assertEqual(
            bands,
            [
                {
                    "id": result[0]["id"],
                    "regrettable_column_name": "Pythonistas",
                    "popularity": 1000,
                    "manager_fk": None,
                },
                {
                    "id": result[1]["id"],
                    "regrettable_column_name": "Rustaceans",
                    "popularity": 500,
                    "manager_fk": None,
                },
            ],
        )

        Band.delete().where(Band.name == "Rustaceans").run_sync()

        bands = Band.select().run_sync()
        self.assertEqual(
            bands,
            [
                {
                    "id": result[0]["id"],
                    "regrettable_column_name": "Pythonistas",
                    "popularity": 1000,
                    "manager_fk": None,
                }
            ],
        )
