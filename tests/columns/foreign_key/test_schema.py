import datetime
from unittest import TestCase

from piccolo.columns import Date, ForeignKey, Varchar
from piccolo.schema import SchemaManager
from piccolo.table import Table, create_db_tables_sync
from tests.base import engines_only


class Manager(Table, schema="schema_1"):
    name = Varchar(length=50)


class Band(Table, schema="schema_1"):
    name = Varchar(length=50)
    manager = ForeignKey(Manager)


class Concert(Table, schema="schema_1"):
    start_date = Date()
    band = ForeignKey(Band)


TABLES = [Band, Manager, Concert]


@engines_only("postgres", "cockroach")
class TestForeignKeyWithSchema(TestCase):
    """
    Make sure that foreign keys work with Postgres schemas.
    """

    schema_manager = SchemaManager()
    schema_name = "schema_1"

    def setUp(self) -> None:
        self.schema_manager.create_schema(
            schema_name=self.schema_name
        ).run_sync()
        create_db_tables_sync(*TABLES)

    def tearDown(self) -> None:
        self.schema_manager.drop_schema(
            schema_name=self.schema_name, if_exists=True, cascade=True
        ).run_sync()

    def test_with_schema(self):
        """
        Make sure that foreign keys work with schemas.
        """
        manager = Manager({Manager.name: "Guido"})
        manager.save().run_sync()

        band = Band({Band.manager: manager, Band.name: "Pythonistas"})
        band.save().run_sync()

        concert = Concert(
            {
                Concert.band: band,
                Concert.start_date: datetime.date(year=2023, month=1, day=1),
            }
        )
        concert.save().run_sync()

        #######################################################################
        # Test single level join.

        query = Band.select(
            Band.name,
            Band.manager.name.as_alias("manager_name"),
        )
        self.assertIn('"schema_1"."band"', query.__str__())
        self.assertIn('"schema_1"."manager"', query.__str__())

        response = query.run_sync()
        self.assertListEqual(
            response,
            [{"name": "Pythonistas", "manager_name": "Guido"}],
        )

        #######################################################################
        # Test two level join.

        query = Concert.select(
            Concert.start_date,
            Concert.band.name.as_alias("band_name"),
            Concert.band._.manager._.name.as_alias("manager_name"),
        )
        self.assertIn('"schema_1"."concert"', query.__str__())
        self.assertIn('"schema_1"."band"', query.__str__())
        self.assertIn('"schema_1"."manager"', query.__str__())

        response = query.run_sync()
        self.assertListEqual(
            response,
            [
                {
                    "start_date": datetime.date(2023, 1, 1),
                    "band_name": "Pythonistas",
                    "manager_name": "Guido",
                }
            ],
        )
