from __future__ import annotations

import contextvars
import logging
import pprint
import string
import typing as t
from abc import ABCMeta, abstractmethod

from typing_extensions import Self

from piccolo.querystring import QueryString
from piccolo.utils.sync import run_sync
from piccolo.utils.warnings import Level, colored_string, colored_warning

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.query.base import DDL, Query


logger = logging.getLogger(__name__)
# This is a set to speed up lookups from O(n) when
# using str vs O(1) when using set[str]
VALID_SAVEPOINT_CHARACTERS: t.Final[set[str]] = set(
    string.ascii_letters + string.digits + "-" + "_"
)


def validate_savepoint_name(savepoint_name: str) -> None:
    """Validates a save point's name meets the required character set."""
    if not all(i in VALID_SAVEPOINT_CHARACTERS for i in savepoint_name):
        raise ValueError(
            "Savepoint names can only contain the following characters:"
            f" {VALID_SAVEPOINT_CHARACTERS}"
        )


class BaseBatch(metaclass=ABCMeta):
    @abstractmethod
    async def __aenter__(self: Self, *args, **kwargs) -> Self: ...

    @abstractmethod
    async def __aexit__(self, *args, **kwargs): ...

    @abstractmethod
    def __aiter__(self: Self) -> Self: ...

    @abstractmethod
    async def __anext__(self) -> t.List[t.Dict]: ...


class BaseTransaction(metaclass=ABCMeta):

    __slots__: t.Tuple[str, ...] = tuple()

    @abstractmethod
    async def __aenter__(self, *args, **kwargs): ...

    @abstractmethod
    async def __aexit__(self, *args, **kwargs) -> bool: ...


class BaseAtomic(metaclass=ABCMeta):

    __slots__: t.Tuple[str, ...] = tuple()

    @abstractmethod
    def add(self, *query: t.Union[Query, DDL]): ...

    @abstractmethod
    async def run(self): ...

    @abstractmethod
    def run_sync(self): ...

    @abstractmethod
    def __await__(self): ...


TransactionClass = t.TypeVar("TransactionClass", bound=BaseTransaction)


class Engine(t.Generic[TransactionClass], metaclass=ABCMeta):
    __slots__ = (
        "query_id",
        "log_queries",
        "log_responses",
        "engine_type",
        "min_version_number",
        "current_transaction",
    )

    def __init__(
        self,
        engine_type: str,
        min_version_number: t.Union[int, float],
        log_queries: bool = False,
        log_responses: bool = False,
    ):
        self.log_queries = log_queries
        self.log_responses = log_responses
        self.engine_type = engine_type
        self.min_version_number = min_version_number

        run_sync(self.check_version())
        run_sync(self.prep_database())
        self.query_id = 0

    @abstractmethod
    async def get_version(self) -> float:
        pass

    @abstractmethod
    def get_version_sync(self) -> float:
        pass

    @abstractmethod
    async def prep_database(self):
        pass

    @abstractmethod
    async def batch(
        self,
        query: Query,
        batch_size: int = 100,
        node: t.Optional[str] = None,
    ) -> BaseBatch:
        pass

    @abstractmethod
    async def run_querystring(
        self, querystring: QueryString, in_pool: bool = True
    ):
        pass

    def transform_response_to_dicts(self, results) -> t.List[t.Dict]:
        """
        If the database adapter returns something other than a list of
        dictionaries, it should perform the transformation here.
        """
        return results

    @abstractmethod
    async def run_ddl(self, ddl: str, in_pool: bool = True):
        pass

    @abstractmethod
    def transaction(self, *args, **kwargs) -> TransactionClass:
        pass

    @abstractmethod
    def atomic(self) -> BaseAtomic:
        pass

    async def check_version(self):
        """
        Warn if the database version isn't supported.
        """
        try:
            version_number = await self.get_version()
        except Exception as exception:
            colored_warning(
                f"Unable to fetch server version: {exception}",
                level=Level.high,
            )
            return

        engine_type = self.engine_type.capitalize()
        logger.info(f"Running {engine_type} version {version_number}")
        if version_number and (version_number < self.min_version_number):
            message = (
                f"This version of {self.engine_type} isn't supported "
                f"(< {self.min_version_number}) - some features might not be "
                "available. For instructions on installing databases, see the "
                "Piccolo docs."
            )
            colored_warning(message, stacklevel=3)

    def _connection_pool_warning(self):
        message = (
            f"Connection pooling is not supported for {self.engine_type}."
        )
        logger.warning(message)
        colored_warning(message, stacklevel=3)

    async def start_connection_pool(self):
        """
        The database driver doesn't implement connection pooling.
        """
        self._connection_pool_warning()

    async def close_connection_pool(self):
        """
        The database driver doesn't implement connection pooling.
        """
        self._connection_pool_warning()

    ###########################################################################

    current_transaction: contextvars.ContextVar[t.Optional[TransactionClass]]

    def transaction_exists(self) -> bool:
        """
        Find out if a transaction is currently active.

        :returns:
            ``True`` if a transaction is already active for the current
            asyncio task. This is useful to know, because nested transactions
            aren't currently supported, so you can check if an existing
            transaction is already active, before creating a new one.

        """
        return self.current_transaction.get() is not None

    ###########################################################################
    # Logging queries and responses

    def get_query_id(self) -> int:
        self.query_id += 1
        return self.query_id

    def print_query(self, query_id: int, query: str):
        print(colored_string(f"\nQuery {query_id}:"))
        print(query)

    def print_response(self, query_id: int, response: t.List):
        print(
            colored_string(f"\nQuery {query_id} response:", level=Level.high)
        )
        pprint.pprint(response)
