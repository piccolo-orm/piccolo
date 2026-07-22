import asyncio
import os
import time
import typing

import pytest

from piccolo.engine.finder import engine_finder

# Force UTC regardless of the host's local timezone. Without this, naive
# datetimes get encoded using the host's local offset, causing timezone
# arithmetic tests to fail on any machine that isn't already running UTC.
os.environ["TZ"] = "UTC"
if hasattr(time, "tzset"):
    time.tzset()

# Set in pytest_configure and cleared in pytest_unconfigure.
_postgres_container: typing.Any = None
_cockroach_container: typing.Any = None


def pytest_configure(config: typing.Any) -> None:
    """Start the appropriate testcontainer based on PICCOLO_CONF.

    Runs before collection and before any test-module imports, so PG_* env vars
    are in place when *_conf.py is first imported inside pytest_sessionstart.

    Set TESTCONTAINERS=false to skip and use an external DB via PG_* env vars.
    """
    global _postgres_container, _cockroach_container

    piccolo_conf = os.environ.get("PICCOLO_CONF", "")
    if os.environ.get("TESTCONTAINERS", "true").lower() in (
        "false",
        "0",
        "no",
    ):
        return

    if "cockroach" in piccolo_conf:
        _cockroach_container = _start_cockroach()
    elif "postgres" in piccolo_conf:
        _postgres_container = _start_postgres()
    # No container needed for SQLite


def pytest_unconfigure(config: typing.Any) -> None:
    global _postgres_container, _cockroach_container
    if _postgres_container is not None:
        _postgres_container.stop()
        _postgres_container = None
    if _cockroach_container is not None:
        _cockroach_container.stop()
        _cockroach_container = None


def _start_postgres() -> typing.Any:
    from testcontainers.core.container import DockerContainer
    from testcontainers.core.wait_strategies import ExecWaitStrategy

    pg_version = os.environ.get("TC_POSTGRES_VERSION", "17")
    container = (
        DockerContainer(f"postgres:{pg_version}")
        .with_env("POSTGRES_USER", "piccolo")
        .with_env("POSTGRES_PASSWORD", "piccolo")
        .with_env("POSTGRES_DB", "piccolo")
        .with_exposed_ports(5432)
        .waiting_for(
            ExecWaitStrategy(["pg_isready", "-U", "piccolo", "-d", "piccolo"])
        )
    )
    try:
        container.start()
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "testcontainers: failed to start Postgres. "
            "Ensure Docker is running, or set TESTCONTAINERS=false."
        ) from exc

    host = container.get_container_host_ip()
    port = int(container.get_exposed_port(5432))

    os.environ["PG_HOST"] = host
    os.environ["PG_PORT"] = str(port)
    os.environ["PG_USER"] = "piccolo"
    os.environ["PG_PASSWORD"] = "piccolo"
    os.environ["PG_DATABASE"] = "piccolo"

    asyncio.run(
        _exec_sql(
            host=host,
            port=port,
            user="piccolo",
            password="piccolo",
            database="piccolo",
            sql='CREATE EXTENSION IF NOT EXISTS "uuid-ossp"',
        )
    )
    return container


def _start_cockroach() -> typing.Any:
    from testcontainers.core.container import DockerContainer
    from testcontainers.core.wait_strategies import ExecWaitStrategy

    crdb_version = os.environ.get("TC_COCKROACH_VERSION", "v25.4.3")
    container = (
        DockerContainer(f"cockroachdb/cockroach:{crdb_version}")
        .with_command("start-single-node --insecure")
        .with_exposed_ports(26257)
        .waiting_for(
            ExecWaitStrategy(
                ["cockroach", "sql", "--insecure", "-e", "SELECT 1"]
            )
        )
    )
    try:
        container.start()
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "testcontainers: failed to start CockroachDB. "
            "Ensure Docker is running, or set TESTCONTAINERS=false."
        ) from exc

    host = container.get_container_host_ip()
    port = int(container.get_exposed_port(26257))

    os.environ["PG_HOST"] = host
    os.environ["PG_PORT"] = str(port)
    os.environ["PG_USER"] = "root"
    os.environ["PG_PASSWORD"] = ""
    os.environ["PG_DATABASE"] = "piccolo"

    # CockroachDB starts with 'defaultdb'. Create the piccolo database.
    asyncio.run(
        _exec_sql(
            host=host,
            port=port,
            user="root",
            password=None,
            database="defaultdb",
            sql="CREATE DATABASE IF NOT EXISTS piccolo",
        )
    )
    return container


async def _exec_sql(
    host: str,
    port: int,
    user: str,
    password: typing.Optional[str],
    database: str,
    sql: str,
) -> None:
    import asyncpg

    conn = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
    )
    try:
        await conn.execute(sql)
    finally:
        await conn.close()


async def drop_tables() -> None:
    engine = engine_finder()
    assert engine is not None

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
        "instrument",
        "signing",
        "mega_table",
        "small_table",
    ]

    if engine.engine_type == "sqlite":
        for table in tables:
            await engine._run_in_new_connection(  # type: ignore[attr-defined]
                f"DROP TABLE IF EXISTS {table}"
            )
    else:
        table_str = ", ".join(tables)
        await engine._run_in_new_connection(  # type: ignore[attr-defined]
            f"DROP TABLE IF EXISTS {table_str} CASCADE"
        )


def pytest_sessionstart(session: typing.Any) -> None:
    """
    Make sure all the tables have been dropped, just in case a previous test
    run was aborted part of the way through.

    https://docs.pytest.org/en/latest/reference.html#_pytest.hookspec.pytest_configure
    """
    print("Session starting")
    asyncio.run(drop_tables())


def pytest_sessionfinish(session: typing.Any, exitstatus: typing.Any) -> None:
    """
    https://docs.pytest.org/en/latest/reference.html#_pytest.hookspec.pytest_sessionfinish
    """
    print("Session finishing")


TABLESPACE_NAME = "piccolo_test_space"
TABLESPACE_DIR = "/var/lib/postgresql/testspace"


@pytest.fixture(scope="session")
def custom_tablespace() -> typing.Optional[str]:
    """Provisions a custom Postgres tablespace inside the testcontainer.

    Returns the tablespace name when running against testcontainers Postgres;
    returns None for SQLite, CockroachDB, or external Postgres.

    Tests should skip when None:

        def test_something(custom_tablespace):
            if custom_tablespace is None:
                pytest.skip("requires testcontainers Postgres")
    """
    if _postgres_container is None:
        return None

    # Create directory inside the container.
    # Works whether exec runs as root or postgres:
    #   - root: mkdir (owned root) → chown fixes it
    #   - postgres: mkdir (owned postgres) → chown fails silently (already
    #     correct)
    mkdir_cmd = (
        f"mkdir -p {TABLESPACE_DIR} && "
        f"chown postgres:postgres {TABLESPACE_DIR} 2>/dev/null || true"
    )
    exit_code, output = _postgres_container.exec(["sh", "-c", mkdir_cmd])
    if exit_code != 0:
        raise RuntimeError(f"tablespace dir setup failed: {output.decode()}")

    host = _postgres_container.get_container_host_ip()
    port = int(_postgres_container.get_exposed_port(5432))
    asyncio.run(
        _exec_sql(
            host=host,
            port=port,
            user="piccolo",
            password="piccolo",
            database="piccolo",
            sql=(
                f"CREATE TABLESPACE {TABLESPACE_NAME} "
                f"LOCATION '{TABLESPACE_DIR}'"
            ),
        )
    )
    return TABLESPACE_NAME
