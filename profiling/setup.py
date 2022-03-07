import asyncio

from tables import Band


async def setup():
    await Band.alter().drop_table(if_exists=True)
    await Band.create_table(if_not_exists=True)
    await Band.insert(*[Band(name="test") for _ in range(1000)])


if __name__ == "__main__":
    asyncio.run(setup())
