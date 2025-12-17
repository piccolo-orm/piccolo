from __future__ import annotations

import contextvars
import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Mapping, Optional, Union

from typing_extensions import Self

from piccolo.engine.base import (
    BaseAtomic,
    BaseBatch,
    BaseTransaction,
    Engine,
    validate_savepoint_name,
)
from piccolo.engine.exceptions import TransactionError
from piccolo.query.base import DDL, Query
from piccolo.querystring import QueryString
from piccolo.utils.lazy_loader import LazyLoader
from piccolo.utils.sync import run_sync
from piccolo.utils.warnings import colored_warning

aiomysql = LazyLoader("aiomysql", globals(), "aiomysql")
pymysql = LazyLoader("pymysql", globals(), "pymysql")

if TYPE_CHECKING:  # pragma: no cover
    from aiomysql.connection import Connection
    from aiomysql.cursors import Cursor
    from aiomysql.pool import Pool

    from piccolo.table import Table


# converters and formaters
def backticks_format(querystring: str) -> str:
    return querystring.replace('"', "`")


def convert_list(value: list) -> str:
    if isinstance(value, list):
        return json.dumps(value)
    return value


def convert_bool(value: int) -> bool:
    return bool(int(value)) if value is not None else None


def convert_uuid(value: Any) -> Union[str, uuid.UUID]:
    if isinstance(value, (bytes, bytearray)):
        value = value.decode()
    value = value.strip()
    # check if string is uuid string
    if len(value) == 36 and value.count("-") == 4:
        try:
            return uuid.UUID(value)
        except ValueError:
            return value
    return value


def parse_mysql_datetime(value: str) -> datetime:
    # handle microseconds
    if "." in value:
        fmt = "%Y-%m-%d %H:%M:%S.%f"
    else:
        fmt = "%Y-%m-%d %H:%M:%S"

    return datetime.strptime(value, fmt)


def convert_timestamptz(value: str) -> datetime:
    dt = parse_mysql_datetime(value)
    # attach timezone
    return dt.replace(tzinfo=timezone.utc)


def convert_timestamp(value: str) -> datetime:
    return parse_mysql_datetime(value)


def converters_map() -> dict[str, Any]:
    converters = pymysql.converters.conversions.copy()
    custom_decoders: dict[str, Any] = {
        pymysql.constants.FIELD_TYPE.STRING: convert_uuid,
        pymysql.constants.FIELD_TYPE.VAR_STRING: convert_uuid,
        pymysql.constants.FIELD_TYPE.VARCHAR: convert_uuid,
        pymysql.constants.FIELD_TYPE.CHAR: convert_uuid,
        pymysql.constants.FIELD_TYPE.TINY: convert_bool,
        pymysql.constants.FIELD_TYPE.TIMESTAMP: convert_timestamptz,
        pymysql.constants.FIELD_TYPE.DATETIME: convert_timestamp,
    }
    converters.update(custom_decoders)
    return converters


@dataclass
class AsyncBatch(BaseBatch):
    connection: Connection
    query: Query
    batch_size: int

    _cursor: Optional[Cursor] = None

    @property
    def cursor(self) -> Cursor:
        if not self._cursor:
            raise ValueError("_cursor not set")
        return self._cursor

    async def next(self) -> list[dict]:
        rows = await self.cursor.fetchmany(self.batch_size)
        if not rows:
            return []
        columns = [desc[0] for desc in self.cursor.description]
        result = [dict(zip(columns, row)) for row in rows]
        return await self.query._process_results(result)

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> list[dict]:
        response = await self.next()
        if not response:
            raise StopAsyncIteration()
        return response

    async def __aenter__(self) -> Self:
        querystring = self.query.querystrings[0]
        query, args = querystring.compile_string()

        self._cursor = await self.connection.cursor()
        async with self._cursor as cur:
            await cur.execute(backticks_format(query), args)
        return self

    async def __aexit__(self, exception_type, exception, traceback):
        await self._cursor.close()
        await self.connection.ensure_closed()
        return exception is not None


###############################################################################


class Atomic(BaseAtomic):
    __slots__ = ("engine", "queries")

    def __init__(self, engine: MySQLEngine):
        self.engine = engine
        self.queries: list[Union[Query, DDL]] = []

    def add(self, *query: Union[Query, DDL]):
        self.queries += list(query)

    async def run(self):
        from piccolo.query.methods.objects import Create, GetOrCreate

        try:
            async with self.engine.transaction():
                for query in self.queries:
                    if isinstance(query, (Query, DDL, Create, GetOrCreate)):
                        await query.run()
                    else:
                        raise ValueError("Unrecognized query type")
            self.queries = []
        except Exception as exception:
            self.queries = []
            raise exception from exception

    def run_sync(self):
        return run_sync(self.run())

    def __await__(self):
        return self.run().__await__()


###############################################################################


class Savepoint:
    def __init__(self, name: str, transaction: MySQLTransaction):
        self.name = name
        self.transaction = transaction

    async def rollback_to(self):
        validate_savepoint_name(self.name)
        async with self.transaction.connection.cursor() as cursor:
            await cursor.execute(f"ROLLBACK TO SAVEPOINT `{self.name}`")

    async def release(self):
        validate_savepoint_name(self.name)
        async with self.transaction.connection.cursor() as cursor:
            await cursor.execute(f"RELEASE SAVEPOINT `{self.name}`")


class MySQLTransaction(BaseTransaction):
    __slots__ = (
        "engine",
        "connection",
        "_savepoint_id",
        "_parent",
        "_committed",
        "_rolled_back",
        "context",
    )

    def __init__(self, engine: MySQLEngine, allow_nested: bool = True):
        self.engine = engine
        current_transaction = self.engine.current_transaction.get()

        self._savepoint_id = 0
        self._parent = None
        self._committed = False
        self._rolled_back = False

        if current_transaction:
            if allow_nested:
                self._parent = current_transaction
            else:
                raise TransactionError("Nested transactions not allowed.")

    async def __aenter__(self) -> MySQLTransaction:
        if self._parent:
            return self._parent

        self.connection = await self.get_connection()
        await self.begin()
        self.context = self.engine.current_transaction.set(self)
        return self

    async def get_connection(self):
        if self.engine.pool:
            return await self.engine.pool.acquire()
        else:
            return await self.engine.get_new_connection()

    async def begin(self):
        await self.connection.begin()

    async def commit(self):
        await self.connection.commit()
        self._committed = True

    async def rollback(self):
        await self.connection.rollback()
        self._rolled_back = True

    async def rollback_to(self, savepoint_name: str):
        await Savepoint(name=savepoint_name, transaction=self).rollback_to()

    #########################################################################

    async def savepoint(self, name: Optional[str] = None) -> Savepoint:
        self._savepoint_id += 1
        name = name or f"savepoint_{self._savepoint_id}"
        validate_savepoint_name(name)
        async with self.connection.cursor() as cursor:
            await cursor.execute(f"SAVEPOINT `{name}`")
        return Savepoint(name=name, transaction=self)

    ##########################################################################

    async def __aexit__(self, exception_type, exception, traceback) -> bool:
        if self._parent:
            return exception is None

        if exception:
            if not self._rolled_back:
                await self.rollback()
        else:
            if not self._committed and not self._rolled_back:
                await self.commit()

        if self.engine.pool:
            self.engine.pool.release(self.connection)
        else:
            self.connection.close()

        self.engine.current_transaction.reset(self.context)
        return exception is None


##########################################################################


class MySQLEngine(Engine[MySQLTransaction]):
    """
    Used to connect to MySQL.

    :param config:
        The config dictionary is passed to the underlying database adapter,
        aiomysql. Common arguments you're likely to need are:

        * host
        * port
        * user
        * password
        * db

        For example, ``{'host': 'localhost', 'port': 3306}``.

    :param log_queries:
        If ``True``, all SQL and DDL statements are printed out before being
        run. Useful for debugging.

    :param log_responses:
        If ``True``, the raw response from each query is printed out. Useful
        for debugging.

    :param extra_nodes:
        For now, just for compatibility.

    """

    __slots__ = ("config", "extra_nodes", "pool")

    def __init__(
        self,
        config: dict[str, Any],
        log_queries: bool = False,
        log_responses: bool = False,
        extra_nodes: Optional[Mapping[str, MySQLEngine]] = None,
    ):
        if extra_nodes is None:
            extra_nodes = {}

        self.config = config
        self.log_queries = log_queries
        self.log_responses = log_responses
        self.extra_nodes = extra_nodes
        self.pool: Optional[Pool] = None
        db_name = config.get("db", "unknown")
        self.current_transaction = contextvars.ContextVar(
            f"mysql_current_transaction_{db_name}", default=None
        )
        # converters
        config["conv"] = converters_map()

        super().__init__(
            engine_type="mysql",
            log_queries=log_queries,
            log_responses=log_responses,
            min_version_number=8.4,
        )

    @staticmethod
    def _parse_raw_version_string(version_string: str) -> float:
        version_segment = version_string.split("-")[0]
        major, minor = version_segment.split(".")[:2]
        return float(f"{major}.{minor}")

    async def get_version(self) -> float:
        try:
            response: Sequence[dict] = await self._run_in_new_connection(
                "SELECT VERSION() as server_version"
            )
        except ConnectionRefusedError as exception:
            colored_warning(f"Unable to connect to database - {exception}")
            return 0.0
        else:
            version_string = response[0]["server_version"]
            return self._parse_raw_version_string(
                version_string=version_string
            )

    def get_version_sync(self) -> float:
        return run_sync(self.get_version())

    async def prep_database(self):
        # Some globals for safer MySQL behavior
        await self._run_in_new_connection(
            """
            SET GLOBAL sql_mode = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,NO_ZERO_DATE,NO_ZERO_IN_DATE';
            SET GLOBAL foreign_key_checks = 1;
            SET GLOBAL innodb_strict_mode = ON;
            SET GLOBAL character_set_server = 'utf8mb4';
            SET GLOBAL collation_server = 'utf8mb4_unicode_ci';
            """  # noqa: E501
        )

    async def start_connection_pool(self, **kwargs):
        if self.pool:
            colored_warning(
                "A pool already exists - close it first if you want to create "
                "a new pool.",
            )
        else:
            config = dict(self.config)
            config.update(**kwargs)
            self.pool = await aiomysql.create_pool(**config)

    async def close_connection_pool(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None
        else:
            colored_warning("No pool is running.")

    ##########################################################################

    async def get_new_connection(self) -> Connection:
        connection = await aiomysql.connect(**self.config)
        # Enable autocommit by default
        await connection.autocommit(True)
        return connection

    #########################################################################

    async def _get_inserted_pk(self, cursor, table: type[Table]) -> Any:
        """
        Retrieve the inserted auto-increment primary keys for MySQL.
        """
        initial_id = cursor.lastrowid
        count = cursor.rowcount
        ids = list(range(initial_id, initial_id + count))
        return ids

    async def _run_in_pool(self, query: str, args: list[Any] = []):
        if args is None:
            args = []
        if not self.pool:
            raise ValueError("A pool isn't currently running.")

        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(query, args)
                rows = await cursor.fetchall()
                columns = (
                    [desc[0] for desc in cursor.description]
                    if cursor.description
                    else []
                )
                await connection.autocommit(True)
                return [dict(zip(columns, row)) for row in rows]

    async def _run_in_new_connection(
        self,
        query: str,
        args: list[Any] = [],
        query_type: str = "generic",
        table: Optional[type[Table]] = None,
    ):
        if args is None:
            args = []
        connection = await self.get_new_connection()
        # convert lists
        params = tuple(convert_list(arg) for arg in args)
        try:
            async with connection.cursor() as cursor:
                await cursor.execute(query, params)
                if query_type == "insert":
                    # We can't use the RETURNING clause in MySQL.
                    assert table is not None
                    ids = []
                    for pk in await self._get_inserted_pk(cursor, table):
                        ids.append(
                            {table._meta.primary_key._meta.db_column_name: pk}
                        )
                    return ids
                rows = await cursor.fetchall()
                columns = (
                    [desc[0] for desc in cursor.description]
                    if cursor.description
                    else []
                )
                return [dict(zip(columns, row)) for row in rows]
        finally:
            connection.close()

    async def run_querystring(
        self, querystring: QueryString, in_pool: bool = True
    ):
        query, query_args = querystring.compile_string(
            engine_type=self.engine_type
        )
        query_id = self.get_query_id()

        if self.log_queries:
            self.print_query(query_id=query_id, query=query)

        current_transaction = self.current_transaction.get()
        if current_transaction:
            async with current_transaction.connection.cursor() as cursor:
                await cursor.execute(backticks_format(query), query_args)
                rows = await cursor.fetchall()
        elif in_pool and self.pool:
            rows = await self._run_in_pool(
                query=backticks_format(query),
                args=query_args,
            )
        else:
            rows = await self._run_in_new_connection(
                query=backticks_format(query),
                args=query_args,
                query_type=querystring.query_type,
                table=querystring.table,
            )

        if self.log_responses:
            self.print_response(query_id=query_id, response=rows)

        return rows

    async def run_ddl(self, ddl: str, in_pool: bool = True):
        query_id = self.get_query_id()
        if self.log_queries:
            self.print_query(query_id=query_id, query=ddl)

        current_transaction = self.current_transaction.get()
        if current_transaction:
            async with current_transaction.connection.cursor() as cursor:
                await cursor.execute(backticks_format(ddl))
        elif in_pool and self.pool:
            await self._run_in_pool(backticks_format(ddl))
        else:
            await self._run_in_new_connection(backticks_format(ddl))

    async def batch(
        self, query: Query, batch_size: int = 100, node: Optional[str] = None
    ) -> AsyncBatch:
        engine: Any = self.extra_nodes.get(node) if node else self
        conn = await engine.get_new_connection()
        return AsyncBatch(connection=conn, query=query, batch_size=batch_size)

    def atomic(self) -> Atomic:
        return Atomic(engine=self)

    def transaction(self, allow_nested: bool = True) -> MySQLTransaction:
        return MySQLTransaction(engine=self, allow_nested=allow_nested)
