import asyncio

from tables import Band


async def run_queries():
    await Band.select()


if __name__ == "__main__":
    asyncio.run(run_queries())
