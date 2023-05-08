from unittest import TestCase

from piccolo.columns import Varchar
from piccolo.table import Table
from tests.base import engines_only
from tests.example_apps.music.tables import Manager


class TestCreate(TestCase):
    def test_create_table(self):
        Manager.create_table().run_sync()
        self.assertTrue(Manager.table_exists().run_sync())

        Manager.alter().drop_table().run_sync()


class BandMember(Table):
    name = Varchar(length=50, index=True)


class TestCreateWithIndexes(TestCase):
    def setUp(self):
        BandMember.create_table().run_sync()

    def tearDown(self):
        BandMember.alter().drop_table().run_sync()

    def test_create_table_with_indexes(self):
        index_names = BandMember.indexes().run_sync()
        index_name = BandMember._get_index_name(["name"])
        self.assertIn(index_name, index_names)

    def test_create_if_not_exists_with_indexes(self):
        """
        Make sure that if the same table is created again, with the
        `if_not_exists` flag, then no errors are raised for duplicate indexes
        (i.e. the indexes should also be created with IF NOT EXISTS).
        """
        query = BandMember.create_table(if_not_exists=True)

        # Shouldn't raise any errors:
        query.run_sync()

        self.assertTrue(
            query.ddl[0].__str__().startswith("CREATE TABLE IF NOT EXISTS"),
            query.ddl[1].__str__().startswith("CREATE INDEX IF NOT EXISTS"),
        )


@engines_only("postgres", "cockroach")
class TestCreateWithSchema(TestCase):
    class Band(Table, tablename="band", schema="schema1"):
        name = Varchar(length=50, index=True)

    def setUp(self) -> None:
        Band = self.Band
        Band.raw('CREATE SCHEMA IF NOT EXISTS "schema1"').run_sync()

    def tearDown(self) -> None:
        Band = self.Band
        Band.raw('DROP SCHEMA "schema1" CASCADE').run_sync()

    def test_table_created(self):
        """
        Make sure that tables can be created in specific schemas.
        """
        Band = self.Band
        Band.create_table().run_sync()

        response = Band.raw(
            """
            SELECT COUNT(*)
            FROM "information_schema"."tables"
            WHERE table_schema = 'schema1'
            AND table_name = 'band';
            """
        ).run_sync()

        self.assertListEqual(response, [{"count": 1}])
