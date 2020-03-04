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

    def __eq__(self, value) -> bool:
        """
        This is used by sets for uniqueness checks.
        """
        if not isinstance(value, DiffableTable):
            return False
        return (self.class_name == value.class_name) and (
            self.tablename == value.tablename
        )

    def __str__(self):
        return f"{self.class_name} - {self.tablename}"


@dataclass
class SchemaDiffer:
    """
    Compares two lists of DiffableTables, and returns the list of alter
    statements required to make them match. Asks for user input when it isn't
    sure - for example, whether a column was renamed.
    """

    schema: t.List[DiffableTable]
    schema_snapshot: t.List[DiffableTable]

    @property
    def create_tables(self):
        new_tables: t.List[DiffableTable] = list(
            set(self.schema) - set(self.schema_snapshot)
        )
        return [
            f"manager.add_table('{i.class_name}', tablename='{i.tablename}')"
            for i in new_tables
        ]

    @property
    def drop_tables(self):
        drop_tables: t.List[DiffableTable] = list(
            set(self.schema_snapshot) - set(self.schema)
        )
        return [
            f"manager.drop_table(tablename='{i.tablename}')"
            for i in drop_tables
        ]

    def get_alter_statements(self):
        """
        Call to execute the necessary alter commands on the database.
        """
        # TODO - check for renames
        return chain(self.create_tables, self.drop_tables)


@dataclass
class MigrationManager:
    """
    Each auto generated migration returns a MigrationManager. It contains
    all of the schema changes that migration wants to make.
    """

    add_tables: t.List[DiffableTable] = field(default_factory=list)
    drop_tables: t.List[DiffableTable] = field(default_factory=list)
    add_columns: t.Dict[str, t.List[Column]] = field(
        default_factory=lambda: defaultdict(list)
    )
    drop_columns: t.Dict[str, t.List[str]] = field(
        default_factory=lambda: defaultdict(list)
    )
    alter_columns: t.Dict[str, t.Dict[str, t.Dict[str, t.Any]]] = field(
        default_factory=lambda: defaultdict(
            lambda: defaultdict(lambda: defaultdict(dict))
        )
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
            self.alter_columns[table_class_name][column_name][
                "length"
            ] = length
        if null is not None:
            self.alter_columns[table_class_name][column_name]["null"] = null
        if unique is not None:
            self.alter_columns[table_class_name][column_name][
                "unique"
            ] = unique


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
        """
        :returns:
            A mapping of table class name to a list of columns which have been
            added.
        """
        return set(chain(*[manager.add_tables for manager in self.managers]))

    @property
    def _drop_tables(self) -> t.Set[DiffableTable]:
        """
        :returns:
            A mapping of table class name to a list of columns which have been
            added.
        """
        return set(chain(*[manager.drop_tables for manager in self.managers]))

    @property
    def remaining_tables(self) -> t.List[DiffableTable]:
        return list(self._add_tables - self._drop_tables)

    ###########################################################################

    @property
    def _add_columns(self) -> t.Dict[str, t.List]:
        """
        :returns:
            A mapping of table class name to a list of columns which have been
            added.
        """
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
        """
        :returns:
            A mapping of table class name to a list of columns which have been
            dropped.
        """
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
    def remaining_columns(self) -> t.Dict[str, t.List[Column]]:
        """
        :returns:
            A mapping of the table class name to a list of remaining
            columns.
        """
        return {
            i: list(set(self._add_columns[i]) - set(self._drop_columns[i]))
            for i in self._add_columns.keys()
        }

    ###########################################################################

    @property
    def remaining_alter_columns(
        self,
    ) -> t.Dict[str, t.Dict[str, t.Dict[str, t.Any]]]:
        """
        :returns:
            A mapping of table class name to a list of column kwargs.
        """
        # table -> column -> kwargs
        output: t.Dict[str, t.Dict[str, t.Dict[str, t.Any]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict())
        )

        # We want to update the dict
        for table_class_name, columns in self.remaining_columns.items():
            for manager in self.managers:
                for column_name, kwargs in manager.alter_columns[
                    table_class_name
                ].items():
                    output[table_class_name][column_name].update(kwargs)

        return output

    ###########################################################################

    def get_snapshot(self) -> t.List[DiffableTable]:
        # Step 1 - add up all of the add tables, and remove all of the
        # remove tables.
        remaining_tables = deepcopy(self.remaining_tables)

        # Step 2 - add and remove columns from the remaining tables.
        for table in remaining_tables:
            table.columns = self.remaining_columns[table.class_name]

            for column in table.columns:
                # Step 3 - apply any alterations to columns
                for key, value in self.remaining_alter_columns[
                    table.class_name
                ][column._meta.name].items():
                    setattr(column._meta, key, value)

        return remaining_tables
