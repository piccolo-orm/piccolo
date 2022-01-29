from unittest import TestCase

from piccolo.columns.column_types import JSONB
from piccolo.table import Table
from tests.base import postgres_only


class RecordingStudio(Table):
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
        row = RecordingStudio(facilities='{"a": 1}')
        row.save().run_sync()
        self.assertEqual(row.facilities, '{"a": 1}')

    def test_where(self):
        """
        Test using the where clause to match a subset of rows.
        """
        RecordingStudio.insert(
            RecordingStudio(facilities={"mixing_desk": True}),
            RecordingStudio(facilities=None),
        ).run_sync()

        self.assertEqual(
            RecordingStudio.count()
            .where(RecordingStudio.facilities == {"mixing_desk": True})
            .run_sync(),
            1,
        )

        self.assertEqual(
            RecordingStudio.count()
            .where(RecordingStudio.facilities == '{"mixing_desk": true}')
            .run_sync(),
            1,
        )

        self.assertEqual(
            RecordingStudio.count()
            .where(RecordingStudio.facilities.is_null())
            .run_sync(),
            1,
        )

        self.assertEqual(
            RecordingStudio.count()
            .where(RecordingStudio.facilities.is_not_null())
            .run_sync(),
            1,
        )

    def test_arrow(self):
        """
        Test using the arrow function to retrieve a subset of the JSON.
        """
        RecordingStudio(facilities='{"a": 1}').save().run_sync()
        row = (
            RecordingStudio.select(RecordingStudio.facilities.arrow("a"))
            .first()
            .run_sync()
        )
        self.assertEqual(row["?column?"], "1")

    def test_arrow_as_alias(self):
        """
        Test using the arrow function to retrieve a subset of the JSON.
        """
        RecordingStudio(facilities='{"a": 1}').save().run_sync()
        row = (
            RecordingStudio.select(
                RecordingStudio.facilities.arrow("a").as_alias("a")
            )
            .first()
            .run_sync()
        )
        self.assertEqual(row["a"], "1")

    def test_arrow_where(self):
        """
        Make sure the arrow function can be used within a WHERE clause.
        """
        RecordingStudio(facilities='{"a": 1}').save().run_sync()
        self.assertEqual(
            RecordingStudio.count()
            .where(RecordingStudio.facilities.arrow("a") == "1")
            .run_sync(),
            1,
        )

        self.assertEqual(
            RecordingStudio.count()
            .where(RecordingStudio.facilities.arrow("a") == "2")
            .run_sync(),
            0,
        )

    def test_arrow_first(self):
        """
        Make sure the arrow function can be used with the first clause.
        """
        RecordingStudio.insert(
            RecordingStudio(facilities='{"a": 1}'),
            RecordingStudio(facilities='{"b": 2}'),
        ).run_sync()

        self.assertEqual(
            RecordingStudio.select(
                RecordingStudio.facilities.arrow("a").as_alias("facilities")
            )
            .first()
            .run_sync(),
            {"facilities": "1"},
        )
