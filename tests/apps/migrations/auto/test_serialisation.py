import datetime
from unittest import TestCase
import uuid

from piccolo.apps.migrations.auto.serialisation import (
    deserialise_params,
    serialise_params,
)
from piccolo.custom_types import (
    DateDefault,
    TimeDefault,
    TimestampDefault,
    UUIDDefault,
)


class TesterialiseParams(TestCase):
    def test_time(self):
        params = serialise_params(params={"default": TimeDefault.now})
        self.assertTrue(params["default"] == "TimeDefault.now")

        time = datetime.datetime.now().time()
        params = serialise_params(params={"default": time})
        self.assertTrue(params["default"] == time.isoformat())

    def test_date(self):
        params = serialise_params(params={"default": DateDefault.now})
        self.assertTrue(params["default"] == "DateDefault.now")

        date = datetime.datetime.now().date()
        params = serialise_params(params={"default": date})
        self.assertTrue(params["default"] == date.isoformat())

    def test_timestamp(self):
        params = serialise_params(params={"default": TimestampDefault.now})
        self.assertTrue(params["default"] == "TimestampDefault.now")

        _datetime = datetime.datetime.now()
        params = serialise_params(params={"default": _datetime})
        self.assertTrue(params["default"] == _datetime.isoformat())

    def test_uuid(self):
        params = serialise_params(params={"default": UUIDDefault.uuid4})
        self.assertTrue(params["default"] == "UUIDDefault.uuid4")

        _uuid = uuid.uuid4()
        params = serialise_params(params={"default": _uuid})
        self.assertTrue(params["default"] == str(_uuid))


class TestDeserialiseParams(TestCase):
    def test_time(self):
        params = deserialise_params(
            "Time", params={"default": "TimeDefault.now"}
        )
        self.assertTrue(params["default"] == TimeDefault.now)

        time = datetime.datetime.now().time()
        params = deserialise_params(
            "Time", params={"default": time.isoformat()}
        )
        self.assertTrue(params["default"] == time)

    def test_date(self):
        params = deserialise_params(
            "Date", params={"default": "DateDefault.now"}
        )
        self.assertTrue(params["default"] == DateDefault.now)

        date = datetime.datetime.now().date()
        params = deserialise_params(
            "Date", params={"default": date.isoformat()},
        )
        self.assertTrue(params["default"] == date)

    def test_timestamp(self):
        params = deserialise_params(
            "Timestamp", params={"default": "TimestampDefault.now"}
        )
        self.assertTrue(params["default"] == TimestampDefault.now)

        _datetime = datetime.datetime.now()
        params = deserialise_params(
            "Timestamp", params={"default": _datetime.isoformat()},
        )
        self.assertTrue(params["default"] == _datetime)

    def test_uuid(self):
        params = deserialise_params(
            "UUID", params={"default": "UUIDDefault.uuid4"}
        )
        self.assertTrue(params["default"] == UUIDDefault.uuid4)

        params = deserialise_params(
            "UUID", params={"default": str(uuid.uuid4())}
        )
        self.assertTrue(isinstance(params["default"], uuid.UUID))
