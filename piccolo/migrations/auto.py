from __future__ import annotations
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from inspect import isclass
from itertools import chain
import typing as t

from piccolo.columns import Column
from piccolo.columns import column_types
from piccolo.table import Table


@dataclass
class AlterColumn:
    table_class_name: str
    column_name: str
    params: t.Dict[str, t.Any]


@dataclass
class DropColumn:
    table_class_name: str
    column_name: str


@dataclass
class AddColumn:
    table_class_name: str
    column_name: str
    params: t.Dict[str, t.Any]


@dataclass
class TableDelta:
    add_columns: t.List[AddColumn] = field(default_factory=list)
    drop_columns: t.List[DropColumn] = field(default_factory=list)
    alter_columns: t.List[AlterColumn] = field(default_factory=list)

    def __eq__(self, value: TableDelta) -> bool:  # type: ignore
        """
        This is mostly for testing purposes.
        """
        return True


def compare_dicts(dict_1, dict_2) -> t.Dict[str, t.Any]:
    """
    Returns a new dictionary which only contains key, value pairs which are in
    the first dictionary and not the second.
    """
    return dict(set(dict_1.items()) - set(dict_2.items()))


def clean_params(params: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    params = deepcopy(params)

    # We currently don't support defaults which are functions.
    default = params.get("default", None)
    if hasattr(default, "__call__"):
        params.pop("default")

    for key, value in params.items():
        # Convert enums into plain values
        if isinstance(value, Enum):
            params[key] = value.value

        # Replace any Table class values into class names
        if isclass(value) and issubclass(value, Table):
            params[key] = value.__name__

    return params


@dataclass
class DiffableTable:
    """
    Represents a Table. When we substract two instances, it returns the
    changes.
    """

    class_name: str
    tablename: str
    columns: t.List[Column] = field(default_factory=list)

    def __post_init__(self):
        self.columns_map: t.Dict[str, Column] = {
            i._meta.name: i for i in self.columns
        }

    def __sub__(self, value: DiffableTable) -> TableDelta:
        if not isinstance(value, DiffableTable):
            raise Exception("Can only diff with other DiffableTable instances")

        add_columns = [
            AddColumn(
                table_class_name=self.class_name,
                column_name=i._meta.name,
                params=i._meta.params,
            )
            for i in (set(self.columns) - set(value.columns))
        ]

        drop_columns = [
            DropColumn(
                table_class_name=self.class_name, column_name=i._meta.name,
            )
            for i in (set(value.columns) - set(self.columns))
        ]

        alter_columns: t.List[AlterColumn] = []

        for column in value.columns:
            # need to compare the params ...
            existing_column = self.columns_map.get(column._meta.name)
            if not existing_column:
                # This is a new column - already captured above.
                continue
            delta = compare_dicts(
                clean_params(existing_column._meta.params),
                clean_params(column._meta.params),
            )
            if delta:
                alter_columns.append(
                    AlterColumn(
                        table_class_name=self.class_name,
                        column_name=column._meta.name,
                        params=delta,
                    )
                )

        return TableDelta(
            add_columns=add_columns,
            drop_columns=drop_columns,
            alter_columns=alter_columns,
        )

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


###############################################################################


@dataclass
class SchemaDiffer:
    """
    Compares two lists of DiffableTables, and returns the list of alter
    statements required to make them match. Asks for user input when it isn't
    sure - for example, whether a column was renamed.
    """

    schema: t.List[DiffableTable]
    schema_snapshot: t.List[DiffableTable]

    def __post_init__(self):
        self.schema_snapshot_map = {
            i.class_name: i for i in self.schema_snapshot
        }

    @property
    def create_tables(self) -> t.List[str]:
        new_tables: t.List[DiffableTable] = list(
            set(self.schema) - set(self.schema_snapshot)
        )

        return [
            f"manager.add_table('{i.class_name}', tablename='{i.tablename}')"
            for i in new_tables
        ]

    @property
    def drop_tables(self) -> t.List[str]:
        drop_tables: t.List[DiffableTable] = list(
            set(self.schema_snapshot) - set(self.schema)
        )
        return [
            f"manager.drop_table(tablename='{i.tablename}')"
            for i in drop_tables
        ]

    @property
    def alter_columns(self) -> t.List[str]:
        response = []
        for table in self.schema:
            snapshot_table = self.schema_snapshot_map.get(
                table.class_name, None
            )
            if not snapshot_table:
                continue
            delta: TableDelta = table - snapshot_table
            for i in delta.alter_columns:
                response.append(
                    f"manager.alter_column(table_class_name='{table.class_name}', column_name='{i.column_name}', params={str(i.params)})"  # noqa
                )
        return response

    @property
    def drop_columns(self) -> t.List[str]:
        response = []
        for table in self.schema:
            snapshot_table = self.schema_snapshot_map.get(
                table.class_name, None
            )
            if not snapshot_table:
                continue
            delta: TableDelta = table - snapshot_table
            for i in delta.drop_columns:
                response.append(
                    f"manager.alter_column(tablename='{table.tablename}', column_name='{i.column_name}')"  # noqa
                )
        return response

    @property
    def add_columns(self) -> t.List[str]:
        response = []
        for table in self.schema:
            snapshot_table = self.schema_snapshot_map.get(
                table.class_name, None
            )
            if not snapshot_table:
                continue
            delta: TableDelta = table - snapshot_table
            for i in delta.add_columns:
                response.append(f"manager.add_column('TODO')")  # noqa
        return response

    @property
    def new_table_columns(self) -> t.List[str]:
        new_tables: t.List[DiffableTable] = list(
            set(self.schema) - set(self.schema_snapshot)
        )

        output = []
        for table in new_tables:
            for column in table.columns:
                # In case we cause subtle bugs:
                params = deepcopy(column._meta.params)
                cleaned_params = clean_params(params)

                output.append(
                    f"manager.add_column(table_class_name='{table.class_name}', column_name='{column._meta.name}', column_class_name='{column.__class__.__name__}', params={str(cleaned_params)})"  # noqa
                )
        return output

    def get_alter_statements(self) -> t.List[str]:
        """
        Call to execute the necessary alter commands on the database.
        """
        # TODO - check for renames
        return list(
            chain(
                self.create_tables,
                self.drop_tables,
                self.new_table_columns,
                self.drop_columns,
                self.add_columns,
                self.alter_columns,
            )
        )


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

    def add_table(
        self, class_name: str, tablename: str, columns: t.List[Column] = []
    ):
        self.add_tables.append(
            DiffableTable(
                class_name=class_name, tablename=tablename, columns=columns
            )
        )

    def drop_table(self, class_name: str, tablename: str):
        self.drop_tables.append(
            DiffableTable(class_name=class_name, tablename=tablename)
        )

    def add_column(
        self,
        table_class_name: str,
        column_name: str,
        column_class_name: str,
        params: t.Dict[str, t.Any] = {},
    ):
        column_class = getattr(column_types, column_class_name)
        column = column_class(**params)
        column._meta.name = column_name
        self.add_columns[table_class_name].append(column)

    def drop_column(self, table_class_name: str, column_name: str):
        self.drop_columns[table_class_name].append(column_name)

    def alter_column(
        self,
        table_class_name: str,
        column_name: str,
        params: t.Dict[str, t.Any],
    ):
        """
        All possible alterations aren't currently supported.
        """
        length = params.get("length")
        null = params.get("null")
        unique = params.get("unique")

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

    async def run(self):
        print("Running MigrationManager ...")


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
