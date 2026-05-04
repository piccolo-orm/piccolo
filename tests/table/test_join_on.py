from unittest import TestCase

from piccolo.columns import Serial, Varchar
from piccolo.table import Table


class Manager(Table):
    id: Serial
    name = Varchar(unique=True)
    email = Varchar(unique=True)


class Band(Table):
    id: Serial
    name = Varchar(unique=True)
    manager_name = Varchar()


class Concert(Table):
    id: Serial
    title = Varchar()
    band_name = Varchar()


class TestJoinOn(TestCase):
    tables = [Manager, Band, Concert]

    def setUp(self):
        for table in self.tables:
            table.create_table().run_sync()

        Manager.insert(
            Manager(name="Guido", email="guido@example.com"),
            Manager(name="Maz", email="maz@example.com"),
            Manager(name="Graydon", email="graydon@example.com"),
        ).run_sync()

        Band.insert(
            Band(name="Pythonistas", manager_name="Guido"),
            Band(name="Rustaceans", manager_name="Graydon"),
        ).run_sync()

        Concert.insert(
            Concert(
                title="Rockfest",
                band_name="Pythonistas",
            ),
        ).run_sync()

    def tearDown(self):
        for table in self.tables:
            table.alter().drop_table().run_sync()

    def test_join_on(self):
        """
        Do a simple join between two tables.
        """
        query = Band.select(
            Band.name,
            Band.manager_name,
            Band.manager_name.join_on(Manager.name).email.as_alias(
                "manager_email"
            ),
        ).order_by(Band.id)

        response = query.run_sync()

        self.assertListEqual(
            response,
            [
                {
                    "name": "Pythonistas",
                    "manager_name": "Guido",
                    "manager_email": "guido@example.com",
                },
                {
                    "name": "Rustaceans",
                    "manager_name": "Graydon",
                    "manager_email": "graydon@example.com",
                },
            ],
        )

    def test_deeper_join(self):
        """
        Do a join between three tables.
        """
        response = (
            Concert.select(
                Concert.title,
                Concert.band_name,
                Concert.band_name.join_on(Band.name)
                .manager_name.join_on(Manager.name)
                .email.as_alias("manager_email"),
            )
            .order_by(Concert.id)
            .run_sync()
        )

        self.assertListEqual(
            response,
            [
                {
                    "title": "Rockfest",
                    "band_name": "Pythonistas",
                    "manager_email": "guido@example.com",
                }
            ],
        )
