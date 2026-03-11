import asyncio

from piccolo.engine.finder import engine_finder

ENGINE = engine_finder()


async def drop_tables():
    tables = [
        "ticket",
        "concert",
        "venue",
        "band",
        "manager",
        "poster",
        "migration",
        "musician",
        "my_table",
        "recording_studio",
        "instrument",
        "shirt",
        "signing",
        "mega_table",
        "small_table",
    ]
    assert ENGINE is not None

    if ENGINE.engine_type == "sqlite":
        # SQLite doesn't allow us to drop more than one table at a time.
        for table in tables:
            await ENGINE._run_in_new_connection(
                f"DROP TABLE IF EXISTS {table}"
            )
    else:
        table_str = ", ".join(tables)
        await ENGINE._run_in_new_connection(
            f"DROP TABLE IF EXISTS {table_str} CASCADE"
        )


def pytest_sessionstart(session):
    """
    Make sure all the tables have been dropped, just in case a previous test
    run was aborted part of the way through.

    https://docs.pytest.org/en/latest/reference.html#_pytest.hookspec.pytest_configure
    """
    print("Session starting")
    asyncio.run(drop_tables())


def pytest_sessionfinish(session, exitstatus):
    """
    https://docs.pytest.org/en/latest/reference.html#_pytest.hookspec.pytest_sessionfinish
    """
    print("Session finishing")
