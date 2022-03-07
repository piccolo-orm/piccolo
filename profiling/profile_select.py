import asyncio

from tables import Band


async def run_queries():
    results = await Band.select()


if __name__ == "__main__":
    asyncio.run(run_queries())
