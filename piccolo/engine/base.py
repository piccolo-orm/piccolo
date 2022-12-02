from __future__ import annotations

import contextvars
import logging
import typing as t
from abc import ABCMeta, abstractmethod

from piccolo.querystring import QueryString
from piccolo.utils.sync import run_sync
from piccolo.utils.warnings import Level, colored_warning

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.query.base import Query


logger = logging.getLogger(__name__)


class Batch:
    pass


TransactionClass = t.TypeVar("TransactionClass")


class Engine(t.Generic[TransactionClass], metaclass=ABCMeta):

    __slots__ = ()

    def __init__(self):
        run_sync(self.check_version())
        run_sync(self.prep_database())

    @property
    @abstractmethod
    def engine_type(self) -> str:
        pass

    @property
    @abstractmethod
    def min_version_number(self) -> float:
        pass

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
    ) -> Batch:
        pass

    @abstractmethod
    async def run_querystring(self, querystring: QueryString, in_pool: bool):
        pass

    @abstractmethod
    async def run_ddl(self, ddl: str, in_pool: bool = True):
        pass

    @abstractmethod
    def transaction(self):
        pass

    @abstractmethod
    def atomic(self):
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
