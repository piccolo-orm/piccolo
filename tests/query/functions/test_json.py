from piccolo.columns import JSONB
from piccolo.query.functions.json import Arrow
from piccolo.table import Table
from piccolo.testing.test_case import AsyncTableTest


class RecordingStudio(Table):
    facilities = JSONB(null=True)


class TestArrow(AsyncTableTest):

    tables = [RecordingStudio]

    async def test_nested(self):
        await RecordingStudio(
            {RecordingStudio.facilities: {"a": {"b": {"c": 1}}}}
        ).save()

        response = await RecordingStudio.select(
            Arrow(Arrow(RecordingStudio.facilities, "a"), "b").as_alias(
                "b_value"
            )
        )
        self.assertListEqual(response, [{"b_value": '{"c": 1}'}])
