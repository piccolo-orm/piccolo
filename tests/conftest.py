import asyncio

from piccolo.engine.finder import engine_finder


ENGINE = engine_finder()


async def drop_tables():
    for table in ["venue", "concert", "band", "manager", "migration"]:
        await ENGINE.run(f"DROP TABLE IF EXISTS {table}")


def pytest_sessionstart(session):
    """
    Make sure all the tables have been dropped.

    https://docs.pytest.org/en/latest/reference.html#_pytest.hookspec.pytest_configure
    """
    print("Session starting")
    asyncio.run(drop_tables())


def pytest_sessionfinish(session, exitstatus):
    """
    https://docs.pytest.org/en/latest/reference.html#_pytest.hookspec.pytest_sessionfinish
    """
    print("Session finishing")
