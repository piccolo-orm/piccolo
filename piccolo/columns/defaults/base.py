from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from piccolo.utils.repr import repr_class_instance


class Default(ABC):
    @property
    @abstractmethod
    def postgres(self) -> str:
        pass

    @property
    @abstractmethod
    def sqlite(self) -> str:
        pass

    @property
    @abstractmethod
    def mysql(self) -> str:
        pass

    @abstractmethod
    def python(self) -> Any:
        pass

    def get_postgres_interval_string(self, attributes: list[str]) -> str:
        """
        Returns a string usable as an interval argument in Postgres e.g.
        "1 day 2 hour".

        :param attributes:
            Date / time attributes to extract from the instance. e.g.
            ['hours', 'minutes']

        """
        interval_components = []
        for attr_name in attributes:
            attr = getattr(self, attr_name, None)
            if attr is not None:
                interval_components.append(f"{attr} {attr_name}")

        return " ".join(interval_components)

    def get_sqlite_interval_string(self, attributes: list[str]) -> str:
        """
        Returns a string usable as an interval argument in SQLite e.g.
        "'-2 hours', '1 days'".

        :param attributes:
            Date / time attributes to extract from the instance. e.g.
            ['hours', 'minutes']

        """
        interval_components = []
        for attr_name in attributes:
            attr = getattr(self, attr_name, None)
            if attr is not None:
                interval_components.append(f"'{attr} {attr_name}'")

        return ", ".join(interval_components)

    def get_mysql_interval_string(self, attributes: list[str]) -> str:
        """
        In MySQL the interval string is different and we should use
        CURRENT_TIMESTAMP + INTERVAL 7 DAY + INTERVAL 10 HOUR etc.
        but I can't get that to work so I convert to seconds and
        use that interval of seconds with the DATE_ADD() function.
        """
        interval_components = []
        for attr_name in attributes:
            attr = getattr(self, attr_name, None)
            if attr is not None:
                if attr_name == "days":
                    attr += attr * 86400
                elif attr_name == "hours":
                    attr += attr * 3600
                elif attr_name == "minutes":
                    attr += attr * 60
                interval_components.append(attr)

        return sum(interval_components)

    def __repr__(self):
        return repr_class_instance(self)

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return hash(self.__str__())


__all__ = ["Default"]
