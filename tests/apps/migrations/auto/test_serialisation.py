from unittest import TestCase

from piccolo.apps.migrations.auto.serialisation import serialise_params

from piccolo.columns.defaults import DateNow, TimeNow, TimestampNow, UUID4


class TestSerialiseParams(TestCase):
    def test_time(self):
        serialised = serialise_params(params={"default": TimeNow()})
        self.assertEqual(serialised.params["default"].__repr__(), "TimeNow()")
        self.assertTrue(len(serialised.extra_imports) == 1)
        self.assertEqual(
            serialised.extra_imports[0].__str__(),
            "from piccolo.columns.defaults.time import TimeNow",
        )

    def test_date(self):
        serialised = serialise_params(params={"default": DateNow()})
        self.assertEqual(serialised.params["default"].__repr__(), "DateNow()")

    def test_timestamp(self):
        serialised = serialise_params(params={"default": TimestampNow()})
        self.assertTrue(
            serialised.params["default"].__repr__() == "TimestampNow()"
        )

    def test_uuid(self):
        serialised = serialise_params(params={"default": UUID4()})
        self.assertTrue(serialised.params["default"].__repr__() == "UUID4()")
