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
from functools import partial, wraps

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


def convert_numeric_in(value: Decimal) -> float:
    """
    Convert any Decimal values into floats.
    """
    return float(value)


def convert_uuid_in(value: uuid.UUID) -> str:
    """
    Converts the UUID value being passed into sqlite.
    """
    return str(value)


def convert_time_in(value: datetime.time) -> str:
    """
    Converts the time value being passed into sqlite.
    """
    return value.isoformat()


def convert_date_in(value: datetime.date) -> str:
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


def convert_timedelta_in(value: datetime.timedelta) -> float:
    """
    Converts the timedelta value being passed into sqlite.
    """
    return value.total_seconds()


def convert_array_in(value: list) -> str:
    """
    Converts a list value into a string (it handles nested lists, and type like
    dateime/ time / date which aren't usually JSON serialisable.).

    """

    def serialise(data: list):
        output = []

        for item in data:
            if isinstance(item, list):
                output.append(serialise(item))
            elif isinstance(
                item, (datetime.datetime, datetime.time, datetime.date)
            ):
                if adapter := ADAPTERS.get(type(item)):
                    output.append(adapter(item))
                else:
                    raise ValueError("The adapter wasn't found.")
            elif item is None or isinstance(item, (str, int, float, list)):
                # We can safely JSON serialise these.
                output.append(item)
            else:
                raise ValueError("We can't currently serialise this value.")

        return output

    return dump_json(serialise(value))


###############################################################################

# Register adapters

ADAPTERS: t.Dict[t.Type, t.Callable[[t.Any], t.Any]] = {
    Decimal: convert_numeric_in,
    uuid.UUID: convert_uuid_in,
    datetime.time: convert_time_in,
    datetime.date: convert_date_in,
    datetime.datetime: convert_datetime_in,
    datetime.timedelta: convert_timedelta_in,
    list: convert_array_in,
}

for value_type, adapter in ADAPTERS.items():
    sqlite3.register_adapter(value_type, adapter)

###############################################################################

# Out


def decode_to_string(converter: t.Callable[[str], t.Any]):
    """
    This means we can use our converters with string and bytes. They are
    passed bytes when used directly via SQLite, and are passed strings when
    used by the array converters.
    """

    @wraps(converter)
    def wrapper(value: t.Union[str, bytes]) -> t.Any:
        if isinstance(value, bytes):
            return converter(value.decode("utf8"))
        elif isinstance(value, str):
            return converter(value)
        else:
            raise ValueError("Unsupported type")

    return wrapper


@decode_to_string
def convert_numeric_out(value: str) -> Decimal:
    """
    Convert float values into Decimals.
    """
    return Decimal(value)


@decode_to_string
def convert_int_out(value: str) -> int:
    """
    Make sure INTEGER values are actually of type ``int``.

    SQLite doesn't enforce that the values in INTEGER columns are actually
    integers - they could be strings ('hello'), or floats (1.0).

    There's not much we can do if the value is something like 'hello' - a
    ``ValueError`` is appropriate in this situation.

    For a value like ``1.0``, it seems reasonable to handle this, and return a
    value of ``1``.

    """
    # We used to use int(float(value)), but it was incorrect, because float has
    # limited precision for large numbers.
    return int(Decimal(value))


@decode_to_string
def convert_uuid_out(value: str) -> uuid.UUID:
    """
    If the value is a uuid, convert it to a UUID instance.
    """
    return uuid.UUID(value)


@decode_to_string
def convert_date_out(value: str) -> datetime.date:
    return datetime.date.fromisoformat(value)


@decode_to_string
def convert_time_out(value: str) -> datetime.time:
    """
    If the value is a time, convert it to a UUID instance.
    """
    return datetime.time.fromisoformat(value)


@decode_to_string
def convert_seconds_out(value: str) -> datetime.timedelta:
    """
    If the value is from a seconds column, convert it to a timedelta instance.
    """
    return datetime.timedelta(seconds=float(value))


@decode_to_string
def convert_boolean_out(value: str) -> bool:
    """
    If the value is from a boolean column, convert it to a bool value.
    """
    return value == "1"


@decode_to_string
def convert_timestamp_out(value: str) -> datetime.datetime:
    """
    If the value is from a timestamp column, convert it to a datetime value.
    """
    return datetime.datetime.fromisoformat(value)


@decode_to_string
def convert_timestamptz_out(value: str) -> datetime.datetime:
    """
    If the value is from a timestamptz column, convert it to a datetime value,
    with a timezone of UTC.
    """
    return datetime.datetime.fromisoformat(value).replace(
        tzinfo=datetime.timezone.utc
    )


@decode_to_string
def convert_array_out(value: str) -> t.List:
    """
    If the value if from an array column, deserialise the string back into a
    list.
    """
    return load_json(value)


def convert_complex_array_out(value: bytes, converter: t.Callable):
    """
    This is used to handle arrays of things like timestamps, which we can't
    just load from JSON without doing additional work to convert the elements
    back into Python objects.
    """
    parsed = load_json(value.decode("utf8"))

    def convert_list(list_value: t.List):
        output = []

        for value in list_value:
            if isinstance(value, list):
                # For nested arrays
                output.append(convert_list(value))
            elif isinstance(value, str):
                output.append(converter(value))
            else:
                output.append(value)

        return output

    if isinstance(parsed, list):
        return convert_list(parsed)
    else:
        return parsed


@decode_to_string
def convert_M2M_out(value: str) -> t.List:
    return value.split(",")


###############################################################################
# Register the basic converters

CONVERTERS = {
    "NUMERIC": convert_numeric_out,
    "INTEGER": convert_int_out,
    "UUID": convert_uuid_out,
    "DATE": convert_date_out,
    "TIME": convert_time_out,
    "SECONDS": convert_seconds_out,
    "BOOLEAN": convert_boolean_out,
    "TIMESTAMP": convert_timestamp_out,
    "TIMESTAMPTZ": convert_timestamptz_out,
    "M2M": convert_M2M_out,
}

for column_name, converter in CONVERTERS.items():
    sqlite3.register_converter(column_name, converter)

###############################################################################
# Register the array converters

# The ARRAY column type handles values which can be easily serialised to and
# from JSON.
sqlite3.register_converter("ARRAY", convert_array_out)

# We have special column types for arrays of timestamps etc, as simply loading
# the JSON isn't sufficient.
for column_name in ("TIMESTAMP", "TIMESTAMPTZ", "DATE", "TIME"):
    sqlite3.register_converter(
        f"ARRAY_{column_name}",
        partial(
            convert_complex_array_out,
            converter=CONVERTERS[column_name],
        ),
    )

###############################################################################


@dataclass
class AsyncBatch(BaseBatch):
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

    def __aiter__(self: Self) -> Self:
        return self

    async def __anext__(self) -> t.List[t.Dict]:
        response = await self.next()
        if response == []:
            raise StopAsyncIteration()
        return response

    async def __aenter__(self: Self) -> Self:
        querystring = self.query.querystrings[0]
        template, template_args = querystring.compile_string()

        self._cursor = await self.connection.execute(template, *template_args)
        return self

    async def __aexit__(self, exception_type, exception, traceback):
        await self.cursor.close()
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


class Atomic(BaseAtomic):
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
        self.queries: t.List[t.Union[Query, DDL]] = []

    def add(self, *query: t.Union[Query, DDL]):
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


class SQLiteTransaction(BaseTransaction):
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

    async def __aexit__(self, exception_type, exception, traceback) -> bool:
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


class SQLiteEngine(Engine[SQLiteTransaction]):
    __slots__ = ("connection_kwargs",)

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

        super().__init__(
            engine_type="sqlite",
            min_version_number=3.25,
            log_queries=log_queries,
            log_responses=log_responses,
        )

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
