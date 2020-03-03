from __future__ import annotations
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from itertools import chain
import typing as t

from piccolo.columns import Column


@dataclass
class TableDelta:
    columns_to_remove: t.List[str] = field(default_factory=list)
    columns_to_add: t.List[Column] = field(default_factory=list)

    def __eq__(self, value: TableDelta) -> bool:  # type: ignore
        """
        This is mostly for testing purposes.
        """
        return True


@dataclass
class DiffableTable:
    """
    Represents a Table. When we substract two instances, it returns the
    changes.
    """

    class_name: str
    tablename: str
    columns: t.List[Column] = field(default_factory=list)

    def __sub__(self, value: DiffableTable) -> TableDelta:
        if not isinstance(value, DiffableTable):
            raise Exception("Can only diff with other DiffableTable instances")

        return TableDelta()

    def __hash__(self) -> int:
        """
        We have to return an integer, which is why convert the string this way.
        """
        return hash(self.class_name + self.tablename)


def default_dict_factory():
    return defaultdict(list)


@dataclass
class MigrationManager:
    """
    Each auto generated migration returns a MigrationManager. It contains
    all of the schema changes that migration wants to make.
    """

    add_tables: t.List[DiffableTable] = field(default_factory=list)
    drop_tables: t.List[DiffableTable] = field(default_factory=list)
    add_columns: t.Dict[str, t.List] = field(
        default_factory=default_dict_factory
    )
    drop_columns: t.Dict[str, t.List] = field(
        default_factory=default_dict_factory
    )
    alter_columns: t.Dict[str, t.Dict[str, t.List]] = field(
        default_factory=default_dict_factory
    )

    def add_table(self, class_name: str, tablename: str):
        self.add_tables.append(
            DiffableTable(class_name=class_name, tablename=tablename)
        )

    def drop_table(self, class_name: str, tablename: str):
        self.drop_tables.append(
            DiffableTable(class_name=class_name, tablename=tablename)
        )

    def add_column(
        self, table_class_name: str, column_name: str, column: Column
    ):
        column._meta.name = column_name
        self.add_columns[table_class_name].append(column)

    def drop_column(self, table_class_name: str, column_name: str):
        self.drop_columns[table_class_name].append(column_name)

    def alter_column(
        self,
        table_class_name: str,
        column_name: str,
        length: t.Optional[int] = None,
        null: t.Optional[bool] = None,
        unique: t.Optional[bool] = None,
    ):
        """
        All possible alterations aren't currently supported.
        """
        if length is not None:
            pass
        if null is not None:
            pass
        if unique is not None:
            pass

    def apply(self):
        """
        Call to execute the necessary alter commands on the database.
        """
        pass


@dataclass
class SchemaSnapshot:
    """
    Adds up a sequence of MigrationManagers, and returns a snapshot of what
    the schema looks like.
    """

    # In ascending order of date created.
    managers: t.List[MigrationManager] = field(default_factory=list)

    ###########################################################################

    @property
    def _add_tables(self) -> t.Set[DiffableTable]:
        return set(chain(*[manager.add_tables for manager in self.managers]))

    @property
    def _drop_tables(self) -> t.Set[DiffableTable]:
        return set(chain(*[manager.drop_tables for manager in self.managers]))

    @property
    def remaining_tables(self) -> t.List[DiffableTable]:
        return list(self._add_tables - self._drop_tables)

    ###########################################################################

    @property
    def _add_columns(self) -> t.Dict[str, t.List]:
        return {
            i.class_name: list(
                chain(
                    *[
                        manager.add_columns[i.class_name]
                        for manager in self.managers
                    ]
                )
            )
            for i in self.remaining_tables
        }

    @property
    def _drop_columns(self) -> t.Dict[str, t.List]:
        return {
            i.class_name: list(
                chain(
                    *[
                        manager.drop_columns[i.class_name]
                        for manager in self.managers
                    ]
                )
            )
            for i in self.remaining_tables
        }

    @property
    def remaining_columns(self) -> t.Dict[str, t.List]:
        return {
            i: list(set(self._add_columns[i]) - set(self._drop_columns[i]))
            for i in self._add_columns.keys()
        }

    ###########################################################################

    def get_snapshot(self) -> t.List[DiffableTable]:
        # Step 1 - add up all of the add tables, and remove all of the
        # remove tables.
        remaining_tables = deepcopy(self.remaining_tables)

        # Step 2 - add and remove columns from the remaining tables.
        for table in remaining_tables:
            table.columns = self.remaining_columns[table.class_name]

        # Step 3 - apply any alterations to columns

        return remaining_tables
