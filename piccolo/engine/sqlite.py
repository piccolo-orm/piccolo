from __future__ import annotations

import contextvars
import datetime
import enum
import os
import sqlite3
import typing as t
import uuid
from dataclasses import dataclass
from decimal import Decimal

from piccolo.engine.base import Batch, Engine, validate_savepoint_name
from piccolo.engine.exceptions import TransactionError
from piccolo.query.base import DDL, Query
from piccolo.querystring import QueryString
from piccolo.utils.encoding import dump_json, load_json
from piccolo.utils.lazy_loader import LazyLoader
from piccolo.utils.sync import run_sync

aiosqlite = LazyLoader("aiosqlite", globals(), "aiosqlite")


if t.TYPE_CHECKING:  # pragma: no cover
    from aiosqlite import Connection, Cursor  # type: ignore

    from piccolo.table import Table

###############################################################################

# We need to register some adapters so sqlite returns types which are more
# consistent with the Postgres engine.


# In


def convert_numeric_in(value):
    """
    Convert any Decimal values into floats.
    """
    return float(value)


def convert_uuid_in(value) -> str:
    """
    Converts the UUID value being passed into sqlite.
    """
    return str(value)


def convert_time_in(value: datetime.time) -> str:
    """
    Converts the time value being passed into sqlite.
    """
    return value.isoformat()


def convert_date_in(value: datetime.date):
    """
    Converts the date value being passed into sqlite.
    """
    return value.isoformat()


def convert_datetime_in(value: datetime.datetime) -> str:
    """
    Converts the datetime into a string. If it's timezone aware, we want to
    convert it to UTC first. This is to replicate Postgres, which stores
    timezone aware datetimes in UTC.
    """
    if value.tzinfo is not None:
        value = value.astimezone(datetime.timezone.utc)
    return str(value)


def convert_timedelta_in(value: datetime.timedelta):
    """
    Converts the timedelta value being passed into sqlite.
    """
    return value.total_seconds()


def convert_array_in(value: list):
    """
    Converts a list value into a string.
    """
    if value and type(value[0]) not in [str, int, float, list]:
        raise ValueError("Can only serialise str, int, float, and list.")

    return dump_json(value)


# Out


def convert_numeric_out(value: bytes) -> Decimal:
    """
    Convert float values into Decimals.
    """
    return Decimal(value.decode("ascii"))


def convert_int_out(value: bytes) -> int:
    """
    Make sure Integer values are actually of type int.
    """
    return int(float(value))


def convert_uuid_out(value: bytes) -> uuid.UUID:
    """
    If the value is a uuid, convert it to a UUID instance.
    """
    return uuid.UUID(value.decode("utf8"))


def convert_date_out(value: bytes) -> datetime.date:
    return datetime.date.fromisoformat(value.decode("utf8"))


def convert_time_out(value: bytes) -> datetime.time:
    """
    If the value is a time, convert it to a UUID instance.
    """
    return datetime.time.fromisoformat(value.decode("utf8"))


def convert_seconds_out(value: bytes) -> datetime.timedelta:
    """
    If the value is from a seconds column, convert it to a timedelta instance.
    """
    return datetime.timedelta(seconds=float(value.decode("utf8")))


def convert_boolean_out(value: bytes) -> bool:
    """
    If the value is from a boolean column, convert it to a bool value.
    """
    _value = value.decode("utf8")
    return _value == "1"


def convert_timestamp_out(value: bytes) -> datetime.datetime:
    """
    If the value is from a timestamp column, convert it to a datetime value.
    """
    return datetime.datetime.fromisoformat(value.decode("utf8"))


def convert_timestamptz_out(value: bytes) -> datetime.datetime:
    """
    If the value is from a timestamptz column, convert it to a datetime value,
    with a timezone of UTC.
    """
    _value = datetime.datetime.fromisoformat(value.decode("utf8"))
    _value = _value.replace(tzinfo=datetime.timezone.utc)
    return _value


def convert_array_out(value: bytes) -> t.List:
    """
    If the value if from an array column, deserialise the string back into a
    list.
    """
    return load_json(value.decode("utf8"))


def convert_M2M_out(value: bytes) -> t.List:
    _value = value.decode("utf8")
    return _value.split(",")


sqlite3.register_converter("Numeric", convert_numeric_out)
sqlite3.register_converter("Integer", convert_int_out)
sqlite3.register_converter("UUID", convert_uuid_out)
sqlite3.register_converter("Date", convert_date_out)
sqlite3.register_converter("Time", convert_time_out)
sqlite3.register_converter("Seconds", convert_seconds_out)
sqlite3.register_converter("Boolean", convert_boolean_out)
sqlite3.register_converter("Timestamp", convert_timestamp_out)
sqlite3.register_converter("Timestamptz", convert_timestamptz_out)
sqlite3.register_converter("Array", convert_array_out)
sqlite3.register_converter("M2M", convert_M2M_out)

sqlite3.register_adapter(Decimal, convert_numeric_in)
sqlite3.register_adapter(uuid.UUID, convert_uuid_in)
sqlite3.register_adapter(datetime.time, convert_time_in)
sqlite3.register_adapter(datetime.date, convert_date_in)
sqlite3.register_adapter(datetime.datetime, convert_datetime_in)
sqlite3.register_adapter(datetime.timedelta, convert_timedelta_in)
sqlite3.register_adapter(list, convert_array_in)

###############################################################################


@dataclass
class AsyncBatch(Batch):
    connection: Connection
    query: Query
    batch_size: int

    # Set internally
    _cursor: t.Optional[Cursor] = None

    @property
    def cursor(self) -> Cursor:
        if not self._cursor:
            raise ValueError("_cursor not set")
        return self._cursor

    async def next(self) -> t.List[t.Dict]:
        data = await self.cursor.fetchmany(self.batch_size)
        return await self.query._process_results(data)

    def __aiter__(self):
        return self

    async def __anext__(self):
        response = await self.next()
        if response == []:
            raise StopAsyncIteration()
        return response

    async def __aenter__(self):
        querystring = self.query.querystrings[0]
        template, template_args = querystring.compile_string()

        self._cursor = await self.connection.execute(template, *template_args)
        return self

    async def __aexit__(self, exception_type, exception, traceback):
        await self._cursor.close()
        await self.connection.close()
        return exception is not None


###############################################################################


class TransactionType(enum.Enum):
    """
    See the `SQLite <https://www.sqlite.org/lang_transaction.html>`_ docs for
    more info.
    """

    deferred = "DEFERRED"
    immediate = "IMMEDIATE"
    exclusive = "EXCLUSIVE"


class Atomic:
    """
    Usage:

    transaction = engine.atomic()
    transaction.add(Foo.create_table())

    # Either:
    transaction.run_sync()
    await transaction.run()
    """

    __slots__ = ("engine", "queries", "transaction_type")

    def __init__(
        self,
        engine: SQLiteEngine,
        transaction_type: TransactionType = TransactionType.deferred,
    ):
        self.engine = engine
        self.transaction_type = transaction_type
        self.queries: t.List[Query] = []

    def add(self, *query: Query):
        self.queries += list(query)

    async def run(self):
        from piccolo.query.methods.objects import Create, GetOrCreate

        try:
            async with self.engine.transaction(
                transaction_type=self.transaction_type
            ):
                for query in self.queries:
                    if isinstance(query, (Query, DDL, Create, GetOrCreate)):
                        await query.run()
                    else:
                        raise ValueError("Unrecognised query")
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
    def __init__(self, name: str, transaction: SQLiteTransaction):
        self.name = name
        self.transaction = transaction

    async def rollback_to(self):
        validate_savepoint_name(self.name)
        await self.transaction.connection.execute(
            f"ROLLBACK TO SAVEPOINT {self.name}"
        )

    async def release(self):
        validate_savepoint_name(self.name)
        await self.transaction.connection.execute(
            f"RELEASE SAVEPOINT {self.name}"
        )


class SQLiteTransaction:
    """
    Used for wrapping queries in a transaction, using a context manager.
    Currently it's async only.

    Usage::

        async with engine.transaction():
            # Run some queries:
            await Band.select().run()

    """

    __slots__ = (
        "engine",
        "context",
        "connection",
        "transaction_type",
        "allow_nested",
        "_savepoint_id",
        "_parent",
        "_committed",
        "_rolled_back",
    )

    def __init__(
        self,
        engine: SQLiteEngine,
        transaction_type: TransactionType = TransactionType.deferred,
        allow_nested: bool = True,
    ):
        """
        :param transaction_type:
            If your transaction just contains ``SELECT`` queries, then use
            ``TransactionType.deferred``. This will give you the best
            performance. When performing ``INSERT``, ``UPDATE``, ``DELETE``
            queries, we recommend using ``TransactionType.immediate`` to
            avoid database locks.
        """
        self.engine = engine
        self.transaction_type = transaction_type
        current_transaction = self.engine.current_transaction.get()

        self._savepoint_id = 0
        self._parent = None
        self._committed = False
        self._rolled_back = False

        if current_transaction:
            if allow_nested:
                self._parent = current_transaction
            else:
                raise TransactionError(
                    "A transaction is already active - nested transactions "
                    "aren't allowed."
                )

    async def __aenter__(self) -> SQLiteTransaction:
        if self._parent is not None:
            return self._parent

        self.connection = await self.get_connection()
        await self.begin()
        self.context = self.engine.current_transaction.set(self)
        return self

    async def get_connection(self):
        return await self.engine.get_connection()

    async def begin(self):
        await self.connection.execute(f"BEGIN {self.transaction_type.value}")

    async def commit(self):
        await self.connection.execute("COMMIT")
        self._committed = True

    async def rollback(self):
        await self.connection.execute("ROLLBACK")
        self._rolled_back = True

    async def rollback_to(self, savepoint_name: str):
        """
        Used to rollback to a savepoint just using the name.
        """
        await Savepoint(name=savepoint_name, transaction=self).rollback_to()

    ###########################################################################

    def get_savepoint_id(self) -> int:
        self._savepoint_id += 1
        return self._savepoint_id

    async def savepoint(self, name: t.Optional[str] = None) -> Savepoint:
        name = name or f"savepoint_{self.get_savepoint_id()}"
        validate_savepoint_name(name)
        await self.connection.execute(f"SAVEPOINT {name}")
        return Savepoint(name=name, transaction=self)

    ###########################################################################

    async def __aexit__(self, exception_type, exception, traceback):
        if self._parent:
            return exception is None

        if exception:
            # The user may have manually rolled it back.
            if not self._rolled_back:
                await self.rollback()
        else:
            # The user may have manually committed it.
            if not self._committed and not self._rolled_back:
                await self.commit()

        await self.connection.close()
        self.engine.current_transaction.reset(self.context)

        return exception is None


###############################################################################


def dict_factory(cursor, row) -> t.Dict:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


class SQLiteEngine(Engine[t.Optional[SQLiteTransaction]]):
    __slots__ = (
        "connection_kwargs",
        "current_transaction",
        "log_queries",
        "log_responses",
    )

    engine_type = "sqlite"
    min_version_number = 3.25

    def __init__(
        self,
        path: str = "piccolo.sqlite",
        log_queries: bool = False,
        log_responses: bool = False,
        **connection_kwargs,
    ) -> None:
        """
        :param path:
            A relative or absolute path to the the SQLite database file (it
            will be created if it doesn't already exist).
        :param log_queries:
            If ``True``, all SQL and DDL statements are printed out before
            being run. Useful for debugging.
        :param log_responses:
            If ``True``, the raw response from each query is printed out.
            Useful for debugging.
        :param connection_kwargs:
            These are passed directly to the database adapter. We recommend
            setting ``timeout`` if you expect your application to process a
            large number of concurrent writes, to prevent queries timing out.
            See Python's `sqlite3 docs <https://docs.python.org/3/library/sqlite3.html#sqlite3.connect>`_
            for more info.

        """  # noqa: E501
        default_connection_kwargs = {
            "database": path,
            "detect_types": sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            "isolation_level": None,
        }

        self.log_queries = log_queries
        self.log_responses = log_responses
        self.connection_kwargs = {
            **default_connection_kwargs,
            **connection_kwargs,
        }

        self.current_transaction = contextvars.ContextVar(
            f"sqlite_current_transaction_{path}", default=None
        )

        super().__init__()

    @property
    def path(self):
        return self.connection_kwargs["database"]

    @path.setter
    def path(self, value: str):
        self.connection_kwargs["database"] = value

    async def get_version(self) -> float:
        return self.get_version_sync()

    def get_version_sync(self) -> float:
        major, minor, _ = sqlite3.sqlite_version_info
        return float(f"{major}.{minor}")

    async def prep_database(self):
        pass

    ###########################################################################

    def remove_db_file(self):
        """
        Use with caution - removes the SQLite file. Useful for testing
        purposes.
        """
        if os.path.exists(self.path):
            os.unlink(self.path)

    def create_db_file(self):
        """
        Create the database file. Useful for testing purposes.
        """
        if os.path.exists(self.path):
            raise Exception(f"Database at {self.path} already exists")
        with open(self.path, "w"):
            pass

    ###########################################################################

    async def batch(
        self, query: Query, batch_size: int = 100, node: t.Optional[str] = None
    ) -> AsyncBatch:
        """
        :param query:
            The database query to run.
        :param batch_size:
            How many rows to fetch on each iteration.
        :param node:
            This is ignored currently, as SQLite runs off a single node. The
            value is here so the API is consistent with Postgres.
        """
        connection = await self.get_connection()
        return AsyncBatch(
            connection=connection, query=query, batch_size=batch_size
        )

    ###########################################################################

    async def get_connection(self) -> Connection:
        connection = await aiosqlite.connect(**self.connection_kwargs)
        connection.row_factory = dict_factory  # type: ignore
        await connection.execute("PRAGMA foreign_keys = 1")
        return connection

    ###########################################################################

    async def _get_inserted_pk(self, cursor, table: t.Type[Table]) -> t.Any:
        """
        If the `pk` column is a non-integer then `ROWID` and `pk` will return
        different types. Need to query by `lastrowid` to get `pk`s in SQLite
        prior to 3.35.0.
        """
        await cursor.execute(
            f"SELECT {table._meta.primary_key._meta.db_column_name} FROM "
            f"{table._meta.tablename} WHERE ROWID = {cursor.lastrowid}"
        )
        response = await cursor.fetchone()
        return response[table._meta.primary_key._meta.db_column_name]

    async def _run_in_new_connection(
        self,
        query: str,
        args: t.Optional[t.List[t.Any]] = None,
        query_type: str = "generic",
        table: t.Optional[t.Type[Table]] = None,
    ):
        if args is None:
            args = []
        async with aiosqlite.connect(**self.connection_kwargs) as connection:
            await connection.execute("PRAGMA foreign_keys = 1")

            connection.row_factory = dict_factory  # type: ignore
            async with connection.execute(query, args) as cursor:
                await connection.commit()

                if query_type == "insert" and self.get_version_sync() < 3.35:
                    # We can't use the RETURNING clause on older versions
                    # of SQLite.
                    assert table is not None
                    pk = await self._get_inserted_pk(cursor, table)
                    return [{table._meta.primary_key._meta.db_column_name: pk}]
                else:
                    return await cursor.fetchall()

    async def _run_in_existing_connection(
        self,
        connection,
        query: str,
        args: t.Optional[t.List[t.Any]] = None,
        query_type: str = "generic",
        table: t.Optional[t.Type[Table]] = None,
    ):
        """
        This is used when a transaction is currently active.
        """
        if args is None:
            args = []
        await connection.execute("PRAGMA foreign_keys = 1")

        connection.row_factory = dict_factory
        async with connection.execute(query, args) as cursor:
            response = await cursor.fetchall()

            if query_type == "insert" and self.get_version_sync() < 3.35:
                # We can't use the RETURNING clause on older versions
                # of SQLite.
                assert table is not None
                pk = await self._get_inserted_pk(cursor, table)
                return [{table._meta.primary_key._meta.db_column_name: pk}]
            else:
                return response

    async def run_querystring(
        self, querystring: QueryString, in_pool: bool = False
    ):
        """
        Connection pools aren't currently supported - the argument is there
        for consistency with other engines.
        """
        query_id = self.get_query_id()

        if self.log_queries:
            self.print_query(query_id=query_id, query=querystring.__str__())

        query, query_args = querystring.compile_string(
            engine_type=self.engine_type
        )

        # If running inside a transaction:
        current_transaction = self.current_transaction.get()
        if current_transaction:
            response = await self._run_in_existing_connection(
                connection=current_transaction.connection,
                query=query,
                args=query_args,
                query_type=querystring.query_type,
                table=querystring.table,
            )
        else:
            response = await self._run_in_new_connection(
                query=query,
                args=query_args,
                query_type=querystring.query_type,
                table=querystring.table,
            )

        if self.log_responses:
            self.print_response(query_id=query_id, response=response)

        return response

    async def run_ddl(self, ddl: str, in_pool: bool = False):
        """
        Connection pools aren't currently supported - the argument is there
        for consistency with other engines.
        """
        query_id = self.get_query_id()

        if self.log_queries:
            self.print_query(query_id=query_id, query=ddl)

        # If running inside a transaction:
        current_transaction = self.current_transaction.get()
        if current_transaction:
            response = await self._run_in_existing_connection(
                connection=current_transaction.connection,
                query=ddl,
            )
        else:
            response = await self._run_in_new_connection(
                query=ddl,
            )

        if self.log_responses:
            self.print_response(query_id=query_id, response=response)

        return response

    def atomic(
        self, transaction_type: TransactionType = TransactionType.deferred
    ) -> Atomic:
        return Atomic(engine=self, transaction_type=transaction_type)

    def transaction(
        self,
        transaction_type: TransactionType = TransactionType.deferred,
        allow_nested: bool = True,
    ) -> SQLiteTransaction:
        """
        Create a new database transaction. See :class:`Transaction`.
        """
        return SQLiteTransaction(
            engine=self,
            transaction_type=transaction_type,
            allow_nested=allow_nested,
        )
