import datetime
from unittest import TestCase

from piccolo.columns import Date, ForeignKey, Varchar
from piccolo.table import Table, create_db_tables_sync, drop_db_tables_sync
from tests.base import engines_only


class Manager(Table, schema="schema1"):
    name = Varchar(length=50)


class Band(Table, schema="schema1"):
    name = Varchar(length=50)
    manager = ForeignKey(Manager)


class Concert(Table, schema="schema1"):
    start_date = Date()
    band = ForeignKey(Band)


TABLES = [Band, Manager, Concert]


@engines_only("postgres", "cockroach")
class TestForeignKeyWithSchema(TestCase):
    """
    Make sure that foreign keys work with Postgres schemas.
    """

    def setUp(self) -> None:
        Band.raw('CREATE SCHEMA IF NOT EXISTS "schema1"').run_sync()
        create_db_tables_sync(*TABLES)

    def tearDown(self) -> None:
        Band.raw('DROP SCHEMA "schema1" CASCADE').run_sync()
        drop_db_tables_sync(*TABLES)

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
        self.assertIn('"schema1"."band"', query.__str__())
        self.assertIn('"schema1"."manager"', query.__str__())

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
            Concert.band.manager.name.as_alias("manager_name"),
        )
        self.assertIn('"schema1"."concert"', query.__str__())
        self.assertIn('"schema1"."band"', query.__str__())
        self.assertIn('"schema1"."manager"', query.__str__())

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
