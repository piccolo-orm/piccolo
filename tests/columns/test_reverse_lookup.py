from unittest import TestCase

from piccolo.columns.column_types import (
    UUID,
    ForeignKey,
    LazyTableReference,
    Varchar,
)
from piccolo.columns.reverse_lookup import ReverseLookup
from piccolo.table import Table, create_db_tables_sync, drop_db_tables_sync


class Manager(Table):
    name = Varchar()
    bands = ReverseLookup(
        LazyTableReference("Band", module_path=__name__),
    )


class Band(Table):
    name = Varchar()
    manager = ForeignKey(Manager)


SIMPLE_SCHEMA = [Manager, Band]


class TestReverseLookup(TestCase):
    def setUp(self):
        create_db_tables_sync(*SIMPLE_SCHEMA, if_not_exists=True)

        Manager.insert(
            Manager(name="Guido"),
            Manager(name="Mark"),
            Manager(name="John"),
        ).run_sync()

        Band.insert(
            Band(name="Pythonistas", manager=1),
            Band(name="Rustaceans", manager=1),
            Band(name="C-Sharps", manager=2),
        ).run_sync()

    def tearDown(self):
        drop_db_tables_sync(*SIMPLE_SCHEMA)

    def test_select_name(self):
        response = Manager.select(
            Manager.name, Manager.bands(Band.name, as_list=True, table=Manager)
        ).run_sync()
        self.assertEqual(
            response,
            [
                {"name": "Guido", "bands": ["Pythonistas", "Rustaceans"]},
                {"name": "Mark", "bands": ["C-Sharps"]},
                {"name": "John", "bands": []},
            ],
        )

    def test_select_multiple(self):
        response = Manager.select(
            Manager.name, Manager.bands(Band.id, Band.name, table=Manager)
        ).run_sync()

        self.assertEqual(
            response,
            [
                {
                    "name": "Guido",
                    "bands": [
                        {"id": 1, "name": "Pythonistas"},
                        {"id": 2, "name": "Rustaceans"},
                    ],
                },
                {"name": "Mark", "bands": [{"id": 3, "name": "C-Sharps"}]},
                {
                    "name": "John",
                    "bands": [],
                },
            ],
        )

    def test_select_multiple_all_columns(self):
        response = Manager.select(
            Manager.name, Manager.bands(table=Manager)
        ).run_sync()

        self.assertEqual(
            response,
            [
                {
                    "name": "Guido",
                    "bands": [
                        {"id": 1, "name": "Pythonistas", "manager": 1},
                        {"id": 2, "name": "Rustaceans", "manager": 1},
                    ],
                },
                {
                    "name": "Mark",
                    "bands": [{"id": 3, "name": "C-Sharps", "manager": 2}],
                },
                {
                    "name": "John",
                    "bands": [],
                },
            ],
        )

    def test_select_id(self):
        response = Manager.select(
            Manager.name, Manager.bands(Band.id, as_list=True, table=Manager)
        ).run_sync()

        self.assertEqual(
            response,
            [
                {"name": "Guido", "bands": [1, 2]},
                {"name": "Mark", "bands": [3]},
                {"name": "John", "bands": []},
            ],
        )

    def test_select_multiple_as_list_error(self):

        with self.assertRaises(ValueError):
            Manager.select(
                Manager.name,
                Manager.bands(Band.id, Band.name, as_list=True, table=Manager),
            ).run_sync()


###############################################################################

# A schema using custom primary keys


class Customer(Table):
    uuid = UUID(primary_key=True)
    name = Varchar()
    concerts = ReverseLookup(
        LazyTableReference("Concert", module_path=__name__),
    )


class Concert(Table):
    uuid = UUID(primary_key=True)
    name = Varchar()
    customer = ForeignKey(Customer)


CUSTOM_PK_SCHEMA = [Customer, Concert]


class TestReverseLookupCustomPrimaryKey(TestCase):
    """
    Make sure the ReverseLookupCustom functionality works correctly
    when the tables have custom primary key columns.
    """

    def setUp(self):
        create_db_tables_sync(*CUSTOM_PK_SCHEMA, if_not_exists=True)

    def tearDown(self):
        drop_db_tables_sync(*CUSTOM_PK_SCHEMA)

    def test_select_custom_primary_key(self):
        Customer.objects().create(name="Bob").run_sync()
        Customer.objects().create(name="Sally").run_sync()
        Customer.objects().create(name="Fred").run_sync()

        bob_pk = (
            Customer.select(Customer.uuid)
            .where(Customer.name == "Bob")
            .first()
            .run_sync()
        )
        sally_pk = (
            Customer.select(Customer.uuid)
            .where(Customer.name == "Sally")
            .first()
            .run_sync()
        )

        Concert.objects().create(
            name="Rockfest", customer=bob_pk["uuid"]
        ).run_sync()
        Concert.objects().create(
            name="Folkfest", customer=bob_pk["uuid"]
        ).run_sync()
        Concert.objects().create(
            name="Classicfest", customer=sally_pk["uuid"]
        ).run_sync()

        response = Customer.select(
            Customer.name,
            Customer.concerts(Concert.name, as_list=True, table=Customer),
        ).run_sync()

        self.assertListEqual(
            response,
            [
                {"name": "Bob", "concerts": ["Rockfest", "Folkfest"]},
                {"name": "Sally", "concerts": ["Classicfest"]},
                {"name": "Fred", "concerts": []},
            ],
        )

        response = Customer.select(
            Customer.name, Customer.concerts(Concert.name, table=Customer)
        ).run_sync()

        self.assertEqual(
            response,
            [
                {
                    "name": "Bob",
                    "concerts": [{"name": "Rockfest"}, {"name": "Folkfest"}],
                },
                {"name": "Sally", "concerts": [{"name": "Classicfest"}]},
                {"name": "Fred", "concerts": []},
            ],
        )
