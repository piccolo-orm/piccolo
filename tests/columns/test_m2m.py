from unittest import TestCase

from piccolo.columns.column_types import (
    UUID,
    ForeignKey,
    LazyTableReference,
    Text,
    Varchar,
)
from piccolo.columns.m2m import M2M
from piccolo.table import Table, create_tables, drop_tables


class Band(Table):
    name = Varchar()
    genres = M2M(LazyTableReference("GenreToBand", module_path=__name__))


class Genre(Table):
    name = Varchar()
    bands = M2M(LazyTableReference("GenreToBand", module_path=__name__))


class GenreToBand(Table):
    band = ForeignKey(Band)
    genre = ForeignKey(Genre)
    reason = Text(help_text="For testing additional columns on join tables.")


TABLES_1 = [Band, Genre, GenreToBand]


class TestM2M(TestCase):
    def setUp(self):
        create_tables(*TABLES_1, if_not_exists=True)

        Band.insert(
            Band(name="Pythonistas"),
            Band(name="Rustaceans"),
            Band(name="C-Sharps"),
        ).run_sync()

        Genre.insert(
            Genre(name="Rock"),
            Genre(name="Folk"),
            Genre(name="Classical"),
        ).run_sync()

        GenreToBand.insert(
            GenreToBand(band=1, genre=1),
            GenreToBand(band=1, genre=2),
            GenreToBand(band=2, genre=2),
            GenreToBand(band=3, genre=1),
            GenreToBand(band=3, genre=3),
        ).run_sync()

    def tearDown(self):
        drop_tables(*TABLES_1)

    def test_select_name(self):
        response = Band.select(
            Band.name, Band.genres(Genre.name, as_list=True)
        ).run_sync()
        self.assertEqual(
            response,
            [
                {"name": "Pythonistas", "genres": ["Rock", "Folk"]},
                {"name": "Rustaceans", "genres": ["Folk"]},
                {"name": "C-Sharps", "genres": ["Rock", "Classical"]},
            ],
        )

        # Now try it in reverse.
        response = Genre.select(
            Genre.name, Genre.bands(Band.name, as_list=True)
        ).run_sync()
        self.assertEqual(
            response,
            [
                {"name": "Rock", "bands": ["Pythonistas", "C-Sharps"]},
                {"name": "Folk", "bands": ["Pythonistas", "Rustaceans"]},
                {"name": "Classical", "bands": ["C-Sharps"]},
            ],
        )

    def test_select_multiple(self):
        response = Band.select(
            Band.name, Band.genres(Genre.id, Genre.name)
        ).run_sync()

        self.assertEqual(
            response,
            [
                {
                    "name": "Pythonistas",
                    "genres": [
                        {"id": 1, "name": "Rock"},
                        {"id": 2, "name": "Folk"},
                    ],
                },
                {"name": "Rustaceans", "genres": [{"id": 2, "name": "Folk"}]},
                {
                    "name": "C-Sharps",
                    "genres": [
                        {"id": 1, "name": "Rock"},
                        {"id": 3, "name": "Classical"},
                    ],
                },
            ],
        )

        # Now try it in reverse.
        response = Genre.select(
            Genre.name, Genre.bands(Band.id, Band.name)
        ).run_sync()

        self.assertEqual(
            response,
            [
                {
                    "name": "Rock",
                    "bands": [
                        {"id": 1, "name": "Pythonistas"},
                        {"id": 3, "name": "C-Sharps"},
                    ],
                },
                {
                    "name": "Folk",
                    "bands": [
                        {"id": 1, "name": "Pythonistas"},
                        {"id": 2, "name": "Rustaceans"},
                    ],
                },
                {
                    "name": "Classical",
                    "bands": [{"id": 3, "name": "C-Sharps"}],
                },
            ],
        )

    def test_select_id(self):
        response = Band.select(
            Band.name, Band.genres(Genre.id, as_list=True)
        ).run_sync()
        self.assertEqual(
            response,
            [
                {"name": "Pythonistas", "genres": [1, 2]},
                {"name": "Rustaceans", "genres": [2]},
                {"name": "C-Sharps", "genres": [1, 3]},
            ],
        )

        # Now try it in reverse.
        response = Genre.select(
            Genre.name, Genre.bands(Band.id, as_list=True)
        ).run_sync()
        self.assertEqual(
            response,
            [
                {"name": "Rock", "bands": [1, 3]},
                {"name": "Folk", "bands": [1, 2]},
                {"name": "Classical", "bands": [3]},
            ],
        )

    def test_add_m2m(self):
        """
        Make sure we can add items to the joining table.
        """
        band: Band = Band.objects().get(Band.name == "Pythonistas").run_sync()
        band.add_m2m(Genre(name="Punk Rock"), m2m=Band.genres).run_sync()

        self.assertTrue(
            Genre.exists().where(Genre.name == "Punk Rock").run_sync()
        )

        self.assertEqual(
            GenreToBand.count()
            .where(
                GenreToBand.band.name == "Pythonistas",
                GenreToBand.genre.name == "Punk Rock",
            )
            .run_sync(),
            1,
        )

    def test_extra_columns_str(self):
        """
        Make sure the ``extra_column_values`` parameter for ``add_m2m`` works
        correctly when the dictionary keys are strings.
        """
        reason = "Their second album was very punk rock."

        band: Band = Band.objects().get(Band.name == "Pythonistas").run_sync()
        band.add_m2m(
            Genre(name="Punk Rock"),
            m2m=Band.genres,
            extra_column_values={
                "reason": "Their second album was very punk rock."
            },
        ).run_sync()

        genre_to_band = (
            GenreToBand.objects()
            .get(
                (GenreToBand.band.name == "Pythonistas")
                & (GenreToBand.genre.name == "Punk Rock")
            )
            .run_sync()
        )

        self.assertEqual(genre_to_band.reason, reason)

    def test_extra_columns_class(self):
        """
        Make sure the ``extra_column_values`` parameter for ``add_m2m`` works
        correctly when the dictionary keys are ``Column`` classes.
        """
        reason = "Their second album was very punk rock."

        band: Band = Band.objects().get(Band.name == "Pythonistas").run_sync()
        band.add_m2m(
            Genre(name="Punk Rock"),
            m2m=Band.genres,
            extra_column_values={
                GenreToBand.reason: "Their second album was very punk rock."
            },
        ).run_sync()

        genre_to_band = (
            GenreToBand.objects()
            .get(
                (GenreToBand.band.name == "Pythonistas")
                & (GenreToBand.genre.name == "Punk Rock")
            )
            .run_sync()
        )

        self.assertEqual(genre_to_band.reason, reason)

    def test_add_m2m_existing(self):
        """
        Make sure we can add an existing element to the joining table.
        """
        band: Band = Band.objects().get(Band.name == "Pythonistas").run_sync()

        genre: Genre = (
            Genre.objects().get(Genre.name == "Classical").run_sync()
        )

        band.add_m2m(genre, m2m=Band.genres).run_sync()

        # We shouldn't have created a duplicate genre in the database.
        self.assertEqual(
            Genre.count().where(Genre.name == "Classical").run_sync(), 1
        )

        self.assertEqual(
            GenreToBand.count()
            .where(
                GenreToBand.band.name == "Pythonistas",
                GenreToBand.genre.name == "Classical",
            )
            .run_sync(),
            1,
        )

    def test_get_m2m(self):
        """
        Make sure we can get related items via the joining table.
        """
        band: Band = Band.objects().get(Band.name == "Pythonistas").run_sync()

        genres = band.get_m2m(Band.genres).run_sync()

        self.assertTrue(all(isinstance(i, Table) for i in genres))

        self.assertEqual([i.name for i in genres], ["Rock", "Folk"])

    def test_remove_m2m(self):
        """
        Make sure we can remove related items via the joining table.
        """
        band: Band = Band.objects().get(Band.name == "Pythonistas").run_sync()

        genre = Genre.objects().get(Genre.name == "Rock").run_sync()

        band.remove_m2m(genre, m2m=Band.genres).run_sync()

        self.assertEqual(
            GenreToBand.count()
            .where(
                GenreToBand.band.name == "Pythonistas",
                GenreToBand.genre.name == "Rock",
            )
            .run_sync(),
            0,
        )

        # Make sure the others weren't removed:
        self.assertEqual(
            GenreToBand.count()
            .where(
                GenreToBand.band.name == "Pythonistas",
                GenreToBand.genre.name == "Folk",
            )
            .run_sync(),
            1,
        )

        self.assertEqual(
            GenreToBand.count()
            .where(
                GenreToBand.band.name == "C-Sharps",
                GenreToBand.genre.name == "Rock",
            )
            .run_sync(),
            1,
        )


###############################################################################

# A schema using custom primary keys


class Customer(Table):
    uuid = UUID(primary_key=True)
    name = Varchar()
    concerts = M2M(
        LazyTableReference("CustomerToConcert", module_path=__name__)
    )


class Concert(Table):
    uuid = UUID(primary_key=True)
    name = Varchar()
    customers = M2M(
        LazyTableReference("CustomerToConcert", module_path=__name__)
    )


class CustomerToConcert(Table):
    customer = ForeignKey(Customer)
    concert = ForeignKey(Concert)


TABLES_2 = [Customer, Concert, CustomerToConcert]


class TestM2MCustomPrimaryKey(TestCase):
    """
    Make sure the M2M functionality works correctly when the tables have custom
    primary key columns.
    """

    def setUp(self):
        create_tables(*TABLES_2, if_not_exists=True)

        bob = Customer.objects().create(name="Bob").run_sync()
        sally = Customer.objects().create(name="Sally").run_sync()
        fred = Customer.objects().create(name="Fred").run_sync()

        rockfest = Concert.objects().create(name="Rockfest").run_sync()
        folkfest = Concert.objects().create(name="Folkfest").run_sync()
        classicfest = Concert.objects().create(name="Classicfest").run_sync()

        CustomerToConcert.insert(
            CustomerToConcert(customer=bob, concert=rockfest),
            CustomerToConcert(customer=bob, concert=classicfest),
            CustomerToConcert(customer=sally, concert=rockfest),
            CustomerToConcert(customer=sally, concert=folkfest),
            CustomerToConcert(customer=fred, concert=classicfest),
        ).run_sync()

    def tearDown(self):
        drop_tables(*TABLES_2)

    def test_select(self):
        response = Customer.select(
            Customer.name, Customer.concerts(Concert.name, as_list=True)
        ).run_sync()

        self.assertListEqual(
            response,
            [
                {"name": "Bob", "concerts": ["Rockfest", "Classicfest"]},
                {"name": "Sally", "concerts": ["Rockfest", "Folkfest"]},
                {"name": "Fred", "concerts": ["Classicfest"]},
            ],
        )

        # Now try it in reverse.
        response = Concert.select(
            Concert.name, Concert.customers(Customer.name, as_list=True)
        ).run_sync()

        self.assertListEqual(
            response,
            [
                {"name": "Rockfest", "customers": ["Bob", "Sally"]},
                {"name": "Folkfest", "customers": ["Sally"]},
                {"name": "Classicfest", "customers": ["Bob", "Fred"]},
            ],
        )

    def test_add_m2m(self):
        """
        Make sure we can add items to the joining table.
        """
        customer: Customer = (
            Customer.objects().get(Customer.name == "Bob").run_sync()
        )
        customer.add_m2m(
            Concert(name="Jazzfest"), m2m=Customer.concerts
        ).run_sync()

        self.assertTrue(
            Concert.exists().where(Concert.name == "Jazzfest").run_sync()
        )

        self.assertEqual(
            CustomerToConcert.count()
            .where(
                CustomerToConcert.customer.name == "Bob",
                CustomerToConcert.concert.name == "Jazzfest",
            )
            .run_sync(),
            1,
        )

    def test_get_m2m(self):
        """
        Make sure we can get related items via the joining table.
        """
        customer: Customer = (
            Customer.objects().get(Customer.name == "Bob").run_sync()
        )

        concerts = customer.get_m2m(Customer.concerts).run_sync()

        self.assertTrue(all(isinstance(i, Table) for i in concerts))

        self.assertCountEqual(
            [i.name for i in concerts], ["Rockfest", "Classicfest"]
        )
