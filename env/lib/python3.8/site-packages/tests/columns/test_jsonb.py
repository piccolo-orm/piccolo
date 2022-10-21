from unittest import TestCase

from piccolo.columns.column_types import JSONB, ForeignKey, Varchar
from piccolo.table import Table
from tests.base import engines_only, engines_skip


class RecordingStudio(Table):
    name = Varchar()
    facilities = JSONB(null=True)


class Instrument(Table):
    name = Varchar()
    studio = ForeignKey(RecordingStudio)


@engines_only("postgres", "cockroach")
class TestJSONB(TestCase):
    def setUp(self):
        RecordingStudio.create_table().run_sync()
        Instrument.create_table().run_sync()

    def tearDown(self):
        Instrument.alter().drop_table().run_sync()
        RecordingStudio.alter().drop_table().run_sync()

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

    def test_arrow(self):
        """
        Test using the arrow function to retrieve a subset of the JSON.
        """
        RecordingStudio(
            name="Abbey Road", facilities='{"mixing_desk": true}'
        ).save().run_sync()

        row = (
            RecordingStudio.select(
                RecordingStudio.facilities.arrow("mixing_desk")
            )
            .first()
            .run_sync()
        )
        self.assertEqual(row["facilities"], "true")

        row = (
            RecordingStudio.select(
                RecordingStudio.facilities.arrow("mixing_desk")
            )
            .output(load_json=True)
            .first()
            .run_sync()
        )
        self.assertEqual(row["facilities"], True)

    def test_arrow_as_alias(self):
        """
        Test using the arrow function to retrieve a subset of the JSON.
        """
        RecordingStudio(
            name="Abbey Road", facilities='{"mixing_desk": true}'
        ).save().run_sync()

        row = (
            RecordingStudio.select(
                RecordingStudio.facilities.arrow("mixing_desk").as_alias(
                    "mixing_desk"
                )
            )
            .first()
            .run_sync()
        )
        self.assertEqual(row["mixing_desk"], "true")

    def test_arrow_where(self):
        """
        Make sure the arrow function can be used within a WHERE clause.
        """
        RecordingStudio(
            name="Abbey Road", facilities='{"mixing_desk": true}'
        ).save().run_sync()

        self.assertEqual(
            RecordingStudio.count()
            .where(RecordingStudio.facilities.arrow("mixing_desk").eq(True))
            .run_sync(),
            1,
        )

        self.assertEqual(
            RecordingStudio.count()
            .where(RecordingStudio.facilities.arrow("mixing_desk").eq(False))
            .run_sync(),
            0,
        )

    def test_arrow_first(self):
        """
        Make sure the arrow function can be used with the first clause.
        """
        RecordingStudio.insert(
            RecordingStudio(facilities='{"mixing_desk": true}'),
            RecordingStudio(facilities='{"mixing_desk": false}'),
        ).run_sync()

        self.assertEqual(
            RecordingStudio.select(
                RecordingStudio.facilities.arrow("mixing_desk").as_alias(
                    "mixing_desk"
                )
            )
            .first()
            .run_sync(),
            {"mixing_desk": "true"},
        )
