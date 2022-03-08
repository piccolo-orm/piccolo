from unittest import TestCase

from piccolo.columns.column_types import JSONB, Varchar
from piccolo.table import Table
from tests.base import postgres_only


class RecordingStudio(Table):
    name = Varchar()
    facilities = JSONB(null=True)


@postgres_only
class TestJSONB(TestCase):
    def setUp(self):
        RecordingStudio.create_table().run_sync()

    def tearDown(self):
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
        self.assertEqual(row["?column?"], "true")

        row = (
            RecordingStudio.select(
                RecordingStudio.facilities.arrow("mixing_desk")
            )
            .output(load_json=True)
            .first()
            .run_sync()
        )
        self.assertEqual(row["?column?"], True)

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
