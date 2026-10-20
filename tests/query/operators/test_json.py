from unittest import TestCase

from piccolo.columns import JSONB
from piccolo.query.operators.json import GetChildElement, GetElementFromPath
from piccolo.table import Table
from tests.base import engines_skip


class RecordingStudio(Table):
    facilities = JSONB(null=True)


@engines_skip("sqlite")
class TestGetChildElement(TestCase):

    def test_query(self):
        """
        Make sure the generated SQL looks correct.
        """
        querystring = GetChildElement(
            GetChildElement(RecordingStudio.facilities, "a"), "b"
        )

        sql, query_args = querystring.compile_string()

        self.assertEqual(
            sql,
            '"recording_studio"."facilities" -> $1 -> $2',
        )

        self.assertListEqual(query_args, ["a", "b"])


@engines_skip("sqlite")
class TestGetElementFromPath(TestCase):

    def test_query(self):
        """
        Make sure the generated SQL looks correct.
        """
        querystring = GetElementFromPath(
            RecordingStudio.facilities, ["a", "b"]
        )

        sql, query_args = querystring.compile_string()

        self.assertEqual(
            sql,
            '"recording_studio"."facilities" #> $1',
        )

        self.assertListEqual(query_args, [["a", "b"]])
