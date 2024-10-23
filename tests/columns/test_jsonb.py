from piccolo.columns.column_types import JSONB, ForeignKey, Varchar
from piccolo.table import Table
from piccolo.testing.test_case import AsyncTableTest, TableTest
from tests.base import engines_only, engines_skip


class RecordingStudio(Table):
    name = Varchar()
    facilities = JSONB(null=True)


class Instrument(Table):
    name = Varchar()
    studio = ForeignKey(RecordingStudio)


@engines_only("postgres", "cockroach")
class TestJSONB(TableTest):
    tables = [RecordingStudio, Instrument]

    def test_json(self):
        """
        Test storing a valid JSON string.
        """
        row = RecordingStudio(
            name="Abbey Road", facilities='{"mixing_desk": true}'
        )
        row.save().run_sync()
        self.assertEqual(row.facilities, '{"mixing_desk": true}')

    @engines_skip("cockroach")
    def test_raw(self):
        """
        Make sure raw queries convert the Python value into a JSON string.
        """
        RecordingStudio.raw(
            "INSERT INTO recording_studio (name, facilities) VALUES ({}, {})",
            "Abbey Road",
            '{"mixing_desk": true}',
        ).run_sync()

        self.assertEqual(
            RecordingStudio.select().run_sync(),
            [
                {
                    "id": 1,
                    "name": "Abbey Road",
                    "facilities": '{"mixing_desk": true}',
                }
            ],
        )

    @engines_only("cockroach")
    def test_raw_alt(self):
        """
        Make sure raw queries convert the Python value into a JSON string.
        """
        result = RecordingStudio.raw(
            "INSERT INTO recording_studio (name, facilities) VALUES ({}, {}) returning id",  # noqa: E501
            "Abbey Road",
            '{"mixing_desk": true}',
        ).run_sync()

        self.assertEqual(
            RecordingStudio.select().run_sync(),
            [
                {
                    "id": result[0]["id"],
                    "name": "Abbey Road",
                    "facilities": '{"mixing_desk": true}',
                }
            ],
        )

    def test_where(self):
        """
        Test using the where clause to match a subset of rows.
        """
        RecordingStudio.insert(
            RecordingStudio(
                name="Abbey Road", facilities={"mixing_desk": True}
            ),
            RecordingStudio(name="ABC Studio", facilities=None),
        ).run_sync()

        self.assertEqual(
            RecordingStudio.select(RecordingStudio.name)
            .where(RecordingStudio.facilities == {"mixing_desk": True})
            .run_sync(),
            [{"name": "Abbey Road"}],
        )

        self.assertEqual(
            RecordingStudio.select(RecordingStudio.name)
            .where(RecordingStudio.facilities == '{"mixing_desk": true}')
            .run_sync(),
            [{"name": "Abbey Road"}],
        )

        self.assertEqual(
            RecordingStudio.select(RecordingStudio.name)
            .where(RecordingStudio.facilities.is_null())
            .run_sync(),
            [{"name": "ABC Studio"}],
        )

        self.assertEqual(
            RecordingStudio.select(RecordingStudio.name)
            .where(RecordingStudio.facilities.is_not_null())
            .run_sync(),
            [{"name": "Abbey Road"}],
        )

    def test_as_alias_join(self):
        """
        Make sure that ``as_alias`` performs correctly when used via a join.
        """
        studio = (
            RecordingStudio.objects()
            .create(name="Abbey Road", facilities={"mixing_desk": True})
            .run_sync()
        )

        Instrument.objects().create(name="Guitar", studio=studio).run_sync()

        response = (
            Instrument.select(
                Instrument.name,
                Instrument.studio.facilities.as_alias("studio_facilities"),
            )
            .output(load_json=True)
            .run_sync()
        )

        self.assertListEqual(
            response,
            [{"name": "Guitar", "studio_facilities": {"mixing_desk": True}}],
        )


@engines_only("postgres", "cockroach")
class TestArrow(AsyncTableTest):
    tables = [RecordingStudio, Instrument]

    async def insert_row(self):
        await RecordingStudio(
            name="Abbey Road", facilities='{"mixing_desk": true}'
        ).save()

    async def test_arrow(self):
        """
        Test using the arrow function to retrieve a subset of the JSON.
        """
        await self.insert_row()

        row = await RecordingStudio.select(
            RecordingStudio.facilities.arrow("mixing_desk")
        ).first()
        assert row is not None
        self.assertEqual(row["facilities"], "true")

        row = await (
            RecordingStudio.select(
                RecordingStudio.facilities.arrow("mixing_desk")
            )
            .output(load_json=True)
            .first()
        )
        assert row is not None
        self.assertEqual(row["facilities"], True)

    async def test_arrow_as_alias(self):
        """
        Test using the arrow function to retrieve a subset of the JSON.
        """
        await self.insert_row()

        row = await RecordingStudio.select(
            RecordingStudio.facilities.arrow("mixing_desk").as_alias(
                "mixing_desk"
            )
        ).first()
        assert row is not None
        self.assertEqual(row["mixing_desk"], "true")

    async def test_square_brackets(self):
        """
        Make sure we can use square brackets instead of calling ``arrow``
        explicitly.
        """
        await self.insert_row()

        row = await RecordingStudio.select(
            RecordingStudio.facilities["mixing_desk"].as_alias("mixing_desk")
        ).first()
        assert row is not None
        self.assertEqual(row["mixing_desk"], "true")

    async def test_multiple_levels_deep(self):
        """
        Make sure elements can be extracted multiple levels deep, and using
        array indexes.
        """
        await RecordingStudio(
            name="Abbey Road",
            facilities={
                "technicians": [
                    {"name": "Alice Jones"},
                    {"name": "Bob Williams"},
                ]
            },
        ).save()

        response = await RecordingStudio.select(
            RecordingStudio.facilities["technicians"][0]["name"].as_alias(
                "technician_name"
            )
        ).output(load_json=True)
        assert response is not None
        self.assertListEqual(response, [{"technician_name": "Alice Jones"}])

    async def test_arrow_where(self):
        """
        Make sure the arrow function can be used within a WHERE clause.
        """
        await self.insert_row()

        self.assertEqual(
            await RecordingStudio.count().where(
                RecordingStudio.facilities.arrow("mixing_desk").eq(True)
            ),
            1,
        )

        self.assertEqual(
            await RecordingStudio.count().where(
                RecordingStudio.facilities.arrow("mixing_desk").eq(False)
            ),
            0,
        )

    async def test_arrow_first(self):
        """
        Make sure the arrow function can be used with the first clause.
        """
        await RecordingStudio.insert(
            RecordingStudio(facilities='{"mixing_desk": true}'),
            RecordingStudio(facilities='{"mixing_desk": false}'),
        )

        self.assertEqual(
            await RecordingStudio.select(
                RecordingStudio.facilities.arrow("mixing_desk").as_alias(
                    "mixing_desk"
                )
            ).first(),
            {"mixing_desk": "true"},
        )


@engines_only("postgres", "cockroach")
class TestFromPath(AsyncTableTest):

    tables = [RecordingStudio, Instrument]

    async def test_from_path(self):
        """
        Make sure ``from_path`` can be used for complex nested data.
        """
        await RecordingStudio(
            name="Abbey Road",
            facilities={
                "technicians": [
                    {"name": "Alice Jones"},
                    {"name": "Bob Williams"},
                ]
            },
        ).save()

        response = await RecordingStudio.select(
            RecordingStudio.facilities.from_path(
                ["technicians", 0, "name"]
            ).as_alias("technician_name")
        ).output(load_json=True)
        assert response is not None
        self.assertListEqual(response, [{"technician_name": "Alice Jones"}])
