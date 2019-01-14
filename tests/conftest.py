import asyncio

import asyncpg
import pytest

from .example_project.tables import DB


async def drop_tables():
    connection = await asyncpg.connect(**DB.config)
    for table in ['venue', 'concert', 'band', 'manager', 'migration']:
        await connection.execute(f'DROP TABLE IF EXISTS {table}')

    await connection.close()


def pytest_sessionstart(session):
    """
    https://docs.pytest.org/en/latest/reference.html#_pytest.hookspec.pytest_configure
    """
    print('Session starting')
    asyncio.run(drop_tables())


# def pytest_sessionfinish(session, exitstatus):
#     """
#     https://docs.pytest.org/en/latest/reference.html#_pytest.hookspec.pytest_sessionfinish
#     """
#     print('Session finishing')
