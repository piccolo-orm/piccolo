import typing as t

from piccolo.engine.finder import engine_finder
from piccolo.table import Table, create_db_tables_sync, drop_db_tables_sync
from tests.base import engine_is, engines_skip

engine = engine_finder()


class M2MBase:
    """
    This allows us to test M2M when the tables are in different schemas
    (public vs non-public).
    """

    band: t.Type[Table]
    genre: t.Type[Table]
    genre_to_band: t.Type[Table]
    all_tables: t.List[t.Type[Table]]

    def setUp(self):
        Band = self.band
        Genre = self.genre
        GenreToBand = self.genre_to_band

        create_db_tables_sync(*self.all_tables, if_not_exists=True)

        if engine_is("cockroach"):
            bands = (
                Band.insert(
                    Band(name="Pythonistas"),
                    Band(name="Rustaceans"),
                    Band(name="C-Sharps"),
                )
                .returning(Band.id)
                .run_sync()
            )

            genres = (
                Genre.insert(
                    Genre(name="Rock"),
                    Genre(name="Folk"),
                    Genre(name="Classical"),
                )
                .returning(Genre.id)
                .run_sync()
            )

            GenreToBand.insert(
                GenreToBand(band=bands[0]["id"], genre=genres[0]["id"]),
                GenreToBand(band=bands[0]["id"], genre=genres[1]["id"]),
                GenreToBand(band=bands[1]["id"], genre=genres[1]["id"]),
                GenreToBand(band=bands[2]["id"], genre=genres[0]["id"]),
                GenreToBand(band=bands[2]["id"], genre=genres[2]["id"]),
            ).run_sync()
        else:
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
        drop_db_tables_sync(*self.all_tables)

    @engines_skip("cockroach")
    def test_select_name(self):
        """
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg
        """  # noqa: E501
        Band = self.band
        Genre = self.genre

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

    @engines_skip("cockroach")
    def test_no_related(self):
        """
        Make sure it still works correctly if there are no related values.
        """
        """
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg
        """  # noqa: E501
        Band = self.band
        Genre = self.genre
        GenreToBand = self.genre_to_band

        GenreToBand.delete(force=True).run_sync()

        # Try it with a list response
        response = Band.select(
            Band.name, Band.genres(Genre.name, as_list=True)
        ).run_sync()

        self.assertEqual(
            response,
            [
                {"name": "Pythonistas", "genres": []},
                {"name": "Rustaceans", "genres": []},
                {"name": "C-Sharps", "genres": []},
            ],
        )

        # Also try it with a nested response
        response = Band.select(
            Band.name, Band.genres(Genre.id, Genre.name)
        ).run_sync()
        self.assertEqual(
            response,
            [
                {"name": "Pythonistas", "genres": []},
                {"name": "Rustaceans", "genres": []},
                {"name": "C-Sharps", "genres": []},
            ],
        )

    @engines_skip("cockroach")
    def test_select_multiple(self):
        """
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg
        """  # noqa: E501
        Band = self.band
        Genre = self.genre

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

    @engines_skip("cockroach")
    def test_select_id(self):
        """
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg
        """  # noqa: E501
        Band = self.band
        Genre = self.genre

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

    @engines_skip("cockroach")
    def test_select_all_columns(self):
        """
        Make sure ``all_columns`` can be passed in as an argument. ``M2M``
        should flatten the arguments. Reported here:

        https://github.com/piccolo-orm/piccolo/issues/728

        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg

        """  # noqa: E501
        Band = self.band
        Genre = self.genre

        response = Band.select(
            Band.name, Band.genres(Genre.all_columns(exclude=(Genre.id,)))
        ).run_sync()
        self.assertEqual(
            response,
            [
                {
                    "name": "Pythonistas",
                    "genres": [
                        {"name": "Rock"},
                        {"name": "Folk"},
                    ],
                },
                {"name": "Rustaceans", "genres": [{"name": "Folk"}]},
                {
                    "name": "C-Sharps",
                    "genres": [
                        {"name": "Rock"},
                        {"name": "Classical"},
                    ],
                },
            ],
        )

    def test_add_m2m(self):
        """
        Make sure we can add items to the joining table.
        """
        Band = self.band
        Genre = self.genre
        GenreToBand = self.genre_to_band

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
        Band = self.band
        Genre = self.genre
        GenreToBand = self.genre_to_band

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
        Band = self.band
        Genre = self.genre
        GenreToBand = self.genre_to_band

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
        Band = self.band
        Genre = self.genre
        GenreToBand = self.genre_to_band

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
        Band = self.band

        band: Band = Band.objects().get(Band.name == "Pythonistas").run_sync()

        genres = band.get_m2m(Band.genres).run_sync()

        self.assertTrue(all(isinstance(i, Table) for i in genres))

        self.assertEqual([i.name for i in genres], ["Rock", "Folk"])

    def test_remove_m2m(self):
        """
        Make sure we can remove related items via the joining table.
        """
        Band = self.band
        Genre = self.genre
        GenreToBand = self.genre_to_band

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
