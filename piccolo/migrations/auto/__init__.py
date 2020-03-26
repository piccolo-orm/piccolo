from __future__ import annotations
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from itertools import chain
import typing as t

from piccolo.columns import Column
from piccolo.migrations.auto.diffable_table import (
    DiffableTable,
    TableDelta,
    DropColumn,
    serialise_params,
)
from piccolo.migrations.auto.operations import RenamedTable, RenameColumn
from piccolo.migrations.auto.migration_manager import MigrationManager


@dataclass
class RenamedTableCollection:
    renamed_tables: t.List[RenamedTable] = field(default_factory=list)

    def append(self, renamed_table: RenamedTable):
        self.renamed_tables.append(renamed_table)

    @property
    def old_class_names(self):
        return [i.old_class_name for i in self.renamed_tables]

    @property
    def new_class_names(self):
        return [i.new_class_name for i in self.renamed_tables]


@dataclass
class SchemaDiffer:
    """
    Compares two lists of DiffableTables, and returns the list of alter
    statements required to make them match. Asks for user input when it isn't
    sure - for example, whether a column was renamed.
    """

    schema: t.List[DiffableTable]
    schema_snapshot: t.List[DiffableTable]

    # Sometimes the SchemaDiffer requires input from a user - for example,
    # asking if a table was renamed or not. When running in non-interactive
    # mode (like in a unittest), we can set a default to be used instead, like
    # 'y'.
    auto_input: t.Optional[str] = None

    ###########################################################################

    def __post_init__(self):
        self.schema_snapshot_map = {
            i.class_name: i for i in self.schema_snapshot
        }
        self.renamed_tables_collection = self.check_renamed_tables()

    def check_renamed_tables(self) -> RenamedTableCollection:
        """
        Work out whether any of the tables were renamed.
        """
        drop_tables: t.List[DiffableTable] = list(
            set(self.schema_snapshot) - set(self.schema)
        )

        new_tables: t.List[DiffableTable] = list(
            set(self.schema) - set(self.schema_snapshot)
        )

        # A mapping of the old table name (i.e. dropped table) to the new
        # table name.
        renamed_tables_collection = RenamedTableCollection()

        if len(drop_tables) == 0 or len(new_tables) == 0:
            # There needs to be at least one dropped table and one created
            # table for a rename to make sense.
            return renamed_tables_collection

        # A renamed table should have at least one column remaining with the
        # same name.
        for new_table in new_tables:
            new_column_names = [i._meta.name for i in new_table.columns]
            for drop_table in drop_tables:
                drop_column_names = [i._meta.name for i in new_table.columns]
                same_column_names = set(new_column_names).intersection(
                    drop_column_names
                )
                if len(same_column_names) > 0:
                    user_response = (
                        self.auto_input
                        if self.auto_input
                        else input(
                            f"Did you rename {drop_table.class_name} to "
                            f"{new_table.class_name}? (y/N)"
                        )
                    )
                    if user_response.lower() == "y":
                        renamed_tables_collection.append(
                            RenamedTable(
                                old_class_name=drop_table.class_name,
                                new_class_name=new_table.class_name,
                                new_tablename=new_table.tablename,
                            )
                        )

        return renamed_tables_collection

    def check_renamed_columns(self):
        """
        Work out whether any of the columns were renamed.
        """
        for table in self.schema:
            snapshot_table = self.schema_snapshot_map.get(
                table.class_name, None
            )
            if not snapshot_table:
                continue
            delta: TableDelta = table - snapshot_table

            if (not delta.add_columns) and (not delta.drop_columns):
                continue

            for add_column in delta.add_columns:
                for drop_column in delta.drop_columns:
                    pass

    ###########################################################################

    @property
    def create_tables(self) -> t.List[str]:
        new_tables: t.List[DiffableTable] = list(
            set(self.schema) - set(self.schema_snapshot)
        )

        # Remove any which are renames
        new_tables = [
            i
            for i in new_tables
            if i.class_name
            not in self.renamed_tables_collection.new_class_names
        ]

        return [
            f"manager.add_table('{i.class_name}', tablename='{i.tablename}')"
            for i in new_tables
        ]

    @property
    def drop_tables(self) -> t.List[str]:
        drop_tables: t.List[DiffableTable] = list(
            set(self.schema_snapshot) - set(self.schema)
        )

        # Remove any which are renames
        drop_tables = [
            i
            for i in drop_tables
            if i.class_name
            not in self.renamed_tables_collection.old_class_names
        ]

        return [
            f"manager.drop_table(tablename='{i.tablename}')"
            for i in drop_tables
        ]

    @property
    def rename_tables(self) -> t.List[str]:
        return [
            f"manager.rename_table(old_class_name='{renamed_table.old_class_name}', new_class_name='{renamed_table.new_class_name}', new_tablename='{renamed_table.new_tablename}')"  # noqa
            for renamed_table in self.renamed_tables_collection.renamed_tables
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
                    f"manager.alter_column(table_class_name='{table.class_name}', tablename='{table.tablename}', column_name='{i.column_name}', params={str(i.params)})"  # noqa
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
                    f"manager.drop_column(table_class_name='{table.class_name}', tablename='{table.tablename}', column_name='{i.column_name}')"  # noqa
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
            for column in delta.add_columns:
                response.append(
                    f"manager.add_column(table_class_name='{table.class_name}', tablename='{table.tablename}', column_name='{column.column_name}', column_class_name='{column.column_class_name}', params={str(column.params)})"  # noqa
                )
        return response

    @property
    def new_table_columns(self) -> t.List[str]:
        new_tables: t.List[DiffableTable] = list(
            set(self.schema) - set(self.schema_snapshot)
        )

        response = []
        for table in new_tables:
            if (
                table.class_name
                in self.renamed_tables_collection.new_class_names
            ):
                continue

            for column in table.columns:
                # In case we cause subtle bugs:
                params = deepcopy(column._meta.params)
                cleaned_params = serialise_params(params)

                response.append(
                    f"manager.add_column(table_class_name='{table.class_name}', tablename='{table.tablename}', column_name='{column._meta.name}', column_class_name='{column.__class__.__name__}', params={str(cleaned_params)})"  # noqa
                )
        return response

    def get_alter_statements(self) -> t.List[str]:
        """
        Call to execute the necessary alter commands on the database.
        """
        return list(
            chain(
                self.create_tables,
                self.drop_tables,
                self.rename_tables,
                self.new_table_columns,
                self.drop_columns,
                self.add_columns,
                self.alter_columns,
            )
        )


def get_table_from_snaphot(migration_id: str):
    """
    This will generate a SchemaSnapshot up to the given migration ID, and
    will return a Table class from that snapshot. This is useful if you want to
    manipulate the data inside your database within a migration, without using
    raw SQL.
    """
    # TODO - tie into commands/migration/new.py code which imports migrations.
    raise NotImplementedError()


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
    def _renamed_tables(self) -> t.List[RenamedTable]:
        return list(
            chain(*[manager.rename_tables for manager in self.managers])
        )

    @property
    def remaining_tables(self) -> t.List[DiffableTable]:
        remaining: t.List[DiffableTable] = deepcopy(
            list(self._add_tables - self._drop_tables)
        )

        for renamed_table in self._renamed_tables:
            tables = [
                i
                for i in remaining
                if i.class_name == renamed_table.old_class_name
            ]
            for table in tables:
                table.class_name = renamed_table.new_class_name
                table.tablename = renamed_table.new_tablename

        return remaining

    ###########################################################################

    @property
    def _all_table_class_names(self) -> t.List[str]:
        """
        :returns:
            All table class names - ones which have been added, and also
            renamed.
        """
        return [i.class_name for i in self._add_tables] + [
            i.new_class_name for i in self._renamed_tables
        ]

    @property
    def _add_columns(self) -> t.Dict[str, t.List[Column]]:
        """
        :returns:
            A mapping of table class name to a list of columns which have been
            added.
        """
        return {
            i: list(
                chain(
                    *[
                        manager.add_columns.columns_for_table_class_name(i)
                        for manager in self.managers
                    ]
                )
            )
            for i in self._all_table_class_names
        }

    @property
    def _drop_columns(self) -> t.Dict[str, t.List[DropColumn]]:
        """
        :returns:
            A mapping of table class name to a list of columns which have been
            dropped.
        """
        return {
            i: list(
                chain(
                    *[
                        manager.drop_columns.for_table_class_name(i)
                        for manager in self.managers
                    ]
                )
            )
            for i in self._all_table_class_names
        }

    @property
    def _rename_columns(self) -> t.Dict[str, t.List[RenameColumn]]:
        """
        :returns:
            A mapping of table class name to a list of RenameColumn.
        """
        return {
            i: list(
                chain(
                    *[
                        manager.rename_columns.for_table_class_name(i)
                        for manager in self.managers
                    ]
                )
            )
            for i in self._all_table_class_names
        }

    @property
    def remaining_columns(self) -> t.Dict[str, t.List[Column]]:
        """
        :returns:
            A mapping of the table class name to a list of remaining
            columns.
        """
        remaining: t.Dict[str, t.List[Column]] = {
            i: list(set(self._add_columns[i]) - set(self._drop_columns[i]))
            for i in self._all_table_class_names
        }

        for table_class_name, rename_columns in self._rename_columns.items():
            for rename_column in rename_columns:
                columns = [
                    i
                    for i in remaining[table_class_name]
                    if i._meta.name == rename_column.old_column_name
                ]
                if columns:
                    columns[0]._meta.name = rename_column.new_column_name

        for renamed_table in self._renamed_tables:
            columns = remaining.pop(renamed_table.old_class_name, [])
            if columns:
                _columns = remaining.get(renamed_table.new_class_name, [])
                _columns.extend(columns)
                remaining[renamed_table.new_class_name] = _columns

        return remaining

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
                for alter_column in manager.alter_columns.for_table_class_name(
                    table_class_name
                ):
                    output[table_class_name][alter_column.column_name].update(
                        alter_column.params
                    )

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
                    column._meta.params.update({key: value})

        return remaining_tables
