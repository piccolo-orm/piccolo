import datetime
import decimal
import uuid
from unittest import TestCase

from piccolo.apps.fixtures.commands.shared import (
    FixtureConfig,
    create_pydantic_fixture_model,
)


class TestShared(TestCase):
    def test_shared(self):
        pydantic_model = create_pydantic_fixture_model(
            fixture_configs=[
                FixtureConfig(
                    app_name="mega",
                    table_class_names=["MegaTable", "SmallTable"],
                )
            ]
        )

        data = {
            "mega": {
                "SmallTable": [{"id": 1, "varchar_col": "Test"}],
                "MegaTable": [
                    {
                        "id": 1,
                        "bigint_col": 1,
                        "boolean_col": True,
                        "bytea_col": b"hello",
                        "date_col": datetime.date(2021, 1, 1),
                        "foreignkey_col": 1,
                        "integer_col": 1,
                        "interval_col": datetime.timedelta(seconds=10),
                        "json_col": '{"a":1}',
                        "jsonb_col": '{"a": 1}',
                        "numeric_col": decimal.Decimal("1.10"),
                        "real_col": 1.100000023841858,
                        "smallint_col": 1,
                        "text_col": "hello",
                        "timestamp_col": datetime.datetime(2021, 1, 1, 0, 0),
                        "timestamptz_col": datetime.datetime(
                            2021, 1, 1, 0, 0, tzinfo=datetime.timezone.utc
                        ),
                        "uuid_col": uuid.UUID(
                            "12783854-c012-4c15-8183-8eecb46f2c4e"
                        ),
                        "varchar_col": "hello",
                        "unique_col": "hello",
                        "null_col": None,
                        "not_null_col": "hello",
                    }
                ],
            }
        }

        model = pydantic_model(**data)
        self.assertEqual(model.mega.SmallTable[0].id, 1)
        self.assertEqual(model.mega.MegaTable[0].id, 1)
