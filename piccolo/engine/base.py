from __future__ import annotations
from abc import abstractmethod, ABCMeta
import typing as t

from piccolo.utils.warnings import colored_warning, Level

if t.TYPE_CHECKING:
    from piccolo.query.base import Query


class Batch:
    pass


class Engine(metaclass=ABCMeta):
    def __init__(self):
        self.check_version()

    @property
    @abstractmethod
    def engine_type(self) -> str:
        pass

    @property
    @abstractmethod
    def min_version_number(self) -> float:
        pass

    @abstractmethod
    def get_version(self) -> float:
        pass

    @abstractmethod
    async def batch(self, query: Query, batch_size: int = 100) -> Batch:
        pass

    def check_version(self):
        """
        Warn if the database version isn't supported.
        """
        try:
            version_number = self.get_version()
        except Exception as exception:
            colored_warning(
                f"Unable to fetch server version: {exception}",
                level=Level.high,
            )
            return

        engine_type = self.engine_type.capitalize()
        print(f"Running {engine_type} version {version_number}")
        if version_number < self.min_version_number:
            message = (
                f"This version of {self.engine_type} isn't supported "
                f"(< {self.min_version_number}) - some features might not be "
                "available. For instructions on installing databases, see the "
                "Piccolo docs."
            )
            colored_warning(message, stacklevel=3)
