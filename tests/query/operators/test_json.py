from unittest import TestCase

from piccolo.columns import JSONB
from piccolo.querystring import QueryString
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


class TestJSONQueryString(TestCase):

    def test_clean_value(self):
        element = GetChildElement(RecordingStudio.facilities, "name")

        # Plain strings should be encoded as JSON
        self.assertEqual(element.clean_value("hello world"), '"hello world"')
        self.assertEqual(element.clean_value("foo"), '"foo"')

        # Already valid JSON strings should be preserved
        self.assertEqual(
            element.clean_value('{"message": "hello world"}'),
            '{"message": "hello world"}',
        )
        self.assertEqual(element.clean_value('["a", "b"]'), '["a", "b"]')
        self.assertEqual(
            element.clean_value('"already quoted"'),
            '"already quoted"',
        )

        # Other python types should be dumped to JSON
        self.assertEqual(
            element.clean_value({"message": "hello world"}),
            '{"message": "hello world"}',
        )
        self.assertEqual(element.clean_value(["a", "b"]), '["a", "b"]')
        self.assertEqual(element.clean_value(123), "123")
        self.assertEqual(element.clean_value(True), "true")
        self.assertEqual(element.clean_value(None), "null")

        # QueryString should be preserved
        qs = QueryString("SELECT 1")
        self.assertEqual(element.clean_value(qs), qs)

    def test_eq_plain_string(self):
        querystring = (
            GetChildElement(RecordingStudio.facilities, "name")
            == "hello world"
        )
        sql, query_args = querystring.compile_string(engine_type="postgres")
        self.assertEqual(
            sql,
            '"recording_studio"."facilities" -> $1 = $2',
        )
        self.assertListEqual(query_args, ["name", '"hello world"'])

    def test_ne_plain_string(self):
        querystring = (
            GetChildElement(RecordingStudio.facilities, "name")
            != "hello world"
        )
        sql, query_args = querystring.compile_string(engine_type="postgres")
        self.assertEqual(
            sql,
            '"recording_studio"."facilities" -> $1 != $2',
        )
        self.assertListEqual(query_args, ["name", '"hello world"'])

    def test_eq_valid_json_string(self):
        querystring = (
            GetChildElement(RecordingStudio.facilities, "info")
            == '{"message": "hello world"}'
        )
        sql, query_args = querystring.compile_string(engine_type="postgres")
        self.assertEqual(
            sql,
            '"recording_studio"."facilities" -> $1 = $2',
        )
        self.assertListEqual(
            query_args, ["info", '{"message": "hello world"}']
        )
