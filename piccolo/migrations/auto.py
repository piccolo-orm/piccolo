from __future__ import annotations
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


@dataclass
class MigrationManager:
    """
    Each auto generated migration returns a MigrationManager. It contains
    all of the schema changes that migration wants to make.
    """

    add_tables: t.List[DiffableTable] = field(default_factory=list)
    drop_tables: t.List[DiffableTable] = field(default_factory=list)
    add_columns: t.List[Column] = field(default_factory=list)
    drop_columns: t.List[Column] = field(default_factory=list)

    def add_table(self, class_name: str, tablename: str):
        self.add_tables.append(
            DiffableTable(class_name=class_name, tablename=tablename)
        )

    def drop_table(self, class_name: str, tablename: str):
        self.drop_tables.append(
            DiffableTable(class_name=class_name, tablename=tablename)
        )

    def add_column(self, column):
        self.add_columns.append(column)

    def drop_column(self):
        self.drop_columns.append(column)

    def alter_column(self):
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
    def _add_tables(self):
        return set(chain(*[manager.add_tables for manager in self.managers]))

    @property
    def _drop_tables(self):
        return set(chain(*[manager.drop_tables for manager in self.managers]))

    @property
    def remaining_tables(self):
        return list(self._add_tables - self._drop_tables)

    ###########################################################################

    @property
    def _add_columns(self):
        return set(chain(*[manager.add_columns for manager in self.managers]))

    @property
    def _drop_columns(self):
        return set(chain(*[manager.drop_columns for manager in self.managers]))

    @property
    def remaining_columns(self):
        return list(self._add_columns - self._drop_columns)

    ###########################################################################

    def get_snapshot(self) -> t.List[DiffableTable]:
        # Step 1 - add up all of the add tables, and remove all of the
        # remove tables.
        remaining_tables = deepcopy(self.remaining_tables)

        # Step 2 - add and remove columns from the remaining tables.
        for table in remaining_tables:
            # TODO - filter columns so they're for the correct table.
            table.columns = self.remaining_columns

        # Step 3 - apply any alterations to columns

        return remaining_tables
