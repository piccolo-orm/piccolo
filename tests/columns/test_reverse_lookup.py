from unittest import TestCase

from piccolo.columns.column_types import (
    UUID,
    ForeignKey,
    LazyTableReference,
    Varchar,
)
from piccolo.columns.reverse_lookup import ReverseLookup
from piccolo.table import Table, create_db_tables_sync, drop_db_tables_sync
from tests.base import engine_is, engines_skip


class Manager(Table):
    name = Varchar()
    bands = ReverseLookup(
        LazyTableReference(
            "Band",
            module_path=__name__,
        ),
        reverse_fk="manager",
    )


class Band(Table):
    name = Varchar()
    manager = ForeignKey(Manager)


SIMPLE_SCHEMA = [Manager, Band]


class TestReverseLookup(TestCase):
    def setUp(self):
        create_db_tables_sync(*SIMPLE_SCHEMA, if_not_exists=True)

        if engine_is("cockroach"):
            managers = (
                Manager.insert(
                    Manager(name="Guido"),
                    Manager(name="Mark"),
                    Manager(name="John"),
                )
                .returning(Manager.id)
                .run_sync()
            )

            Band.insert(
                Band(name="Pythonistas", manager=managers[0]["id"]),
                Band(name="Rustaceans", manager=managers[0]["id"]),
                Band(name="C-Sharps", manager=managers[1]["id"]),
            ).returning(Band.id).run_sync()

        else:
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
            Manager.name, Manager.bands(Band.name, as_list=True)
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
            Manager.name, Manager.bands(Band.id, Band.name)
        ).run_sync()

        if engine_is("cockroach"):
            self.assertEqual(len(response[0]["bands"]), 2)
            self.assertEqual(len(response[1]["bands"]), 1)
            self.assertEqual(len(response[2]["bands"]), 0)
        else:
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
        response = Manager.select(Manager.name, Manager.bands()).run_sync()

        if engine_is("cockroach"):
            self.assertEqual(len(response[0]["bands"]), 2)
            self.assertEqual(len(response[1]["bands"]), 1)
            self.assertEqual(len(response[2]["bands"]), 0)
        else:
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
            Manager.name, Manager.bands(Band.id, as_list=True)
        ).run_sync()

        if engine_is("cockroach"):
            self.assertEqual(len(response[0]["bands"]), 2)
            self.assertEqual(len(response[1]["bands"]), 1)
            self.assertEqual(len(response[2]["bands"]), 0)
        else:
            self.assertEqual(
                response,
                [
                    {"name": "Guido", "bands": [1, 2]},
                    {"name": "Mark", "bands": [3]},
                    {"name": "John", "bands": []},
                ],
            )

    def test_select_multiple_all_columns_descending(self):
        response = Manager.select(
            Manager.name, Manager.bands(descending=True)
        ).run_sync()

        if engine_is("cockroach"):
            self.assertEqual(len(response[0]["bands"]), 2)
            self.assertEqual(len(response[1]["bands"]), 1)
            self.assertEqual(len(response[2]["bands"]), 0)
        else:
            self.assertEqual(
                response,
                [
                    {
                        "name": "Guido",
                        "bands": [
                            {"id": 2, "name": "Rustaceans", "manager": 1},
                            {"id": 1, "name": "Pythonistas", "manager": 1},
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

    def test_select_id_descending(self):
        response = Manager.select(
            Manager.name, Manager.bands(Band.id, as_list=True, descending=True)
        ).run_sync()

        if engine_is("cockroach"):
            self.assertEqual(len(response[0]["bands"]), 2)
            self.assertEqual(len(response[1]["bands"]), 1)
            self.assertEqual(len(response[2]["bands"]), 0)
        else:
            self.assertEqual(
                response,
                [
                    {"name": "Guido", "bands": [2, 1]},
                    {"name": "Mark", "bands": [3]},
                    {"name": "John", "bands": []},
                ],
            )

    def test_select_multiple_as_list_error(self):
        with self.assertRaises(ValueError):
            Manager.select(
                Manager.name,
                Manager.bands(Band.id, Band.name, as_list=True),
            ).run_sync()

    def test_objects_query(self):
        manager = Manager.objects().get(Manager.name == "Guido").run_sync()
        bands = manager.get_reverse_lookup(Manager.bands).run_sync()
        response = {
            "name": manager.name,
            "bands": [i.to_dict() for i in bands],
        }

        if engine_is("cockroach"):
            self.assertEqual(len(response["bands"]), 2)
        else:
            self.assertEqual(
                response,
                {
                    "name": "Guido",
                    "bands": [
                        {"id": 1, "name": "Pythonistas", "manager": 1},
                        {"id": 2, "name": "Rustaceans", "manager": 1},
                    ],
                },
            )


###############################################################################

# A schema using custom primary keys


class Customer(Table):
    uuid = UUID(primary_key=True)
    name = Varchar()
    concerts = ReverseLookup(
        LazyTableReference(
            "Concert",
            module_path=__name__,
        ),
        reverse_fk="customer",
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

    def tearDown(self):
        drop_db_tables_sync(*CUSTOM_PK_SCHEMA)

    @engines_skip("cockroach")
    def test_select_custom_primary_key(self):
        response = Customer.select(
            Customer.name,
            Customer.concerts(Concert.name, as_list=True),
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
            Customer.name, Customer.concerts(Concert.name)
        ).run_sync()

        self.assertEqual(
            response,
            [
                {
                    "name": "Bob",
                    "concerts": [
                        {"name": "Rockfest"},
                        {"name": "Folkfest"},
                    ],
                },
                {"name": "Sally", "concerts": [{"name": "Classicfest"}]},
                {"name": "Fred", "concerts": []},
            ],
        )

        response = Customer.select(
            Customer.name, Customer.concerts(Concert.name, descending=True)
        ).run_sync()

        self.assertEqual(
            response,
            [
                {
                    "name": "Bob",
                    "concerts": [
                        {"name": "Folkfest"},
                        {"name": "Rockfest"},
                    ],
                },
                {"name": "Sally", "concerts": [{"name": "Classicfest"}]},
                {"name": "Fred", "concerts": []},
            ],
        )

    def test_objects_custom_primary_key(self):
        customer_bob = (
            Customer.objects().get(Customer.name == "Bob").run_sync()
        )
        concerts_bob = customer_bob.get_reverse_lookup(
            Customer.concerts
        ).run_sync()

        customer_sally = (
            Customer.objects().get(Customer.name == "Sally").run_sync()
        )
        concerts_sally = customer_sally.get_reverse_lookup(
            Customer.concerts
        ).run_sync()

        customer_fred = (
            Customer.objects().get(Customer.name == "Fred").run_sync()
        )
        concerts_fred = customer_fred.get_reverse_lookup(
            Customer.concerts
        ).run_sync()

        self.assertEqual(len(concerts_bob), 2)
        self.assertEqual(len(concerts_sally), 1)
        self.assertEqual(len(concerts_fred), 0)
