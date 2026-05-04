import asyncio

from viztracer import VizTracer

from piccolo.columns.column_types import Varchar
from piccolo.engine.postgres import PostgresEngine
from piccolo.table import Table

DB = PostgresEngine(config={"database": "piccolo_profile"})


class Band(Table, db=DB):
    name = Varchar()


async def setup():
    await Band.alter().drop_table(if_exists=True)
    await Band.create_table(if_not_exists=True)
    await Band.insert(*[Band(name="test") for _ in range(1000)])


class Trace:
    def __enter__(self):
        self.tracer = VizTracer(log_async=True)
        self.tracer.start()

    def __exit__(self, *args):
        self.tracer.stop()
        self.tracer.save()


async def run_queries():
    await setup()

    with Trace():
        await Band.select()


if __name__ == "__main__":
    asyncio.run(run_queries())
