from __future__ import annotations
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from itertools import chain
import typing as t

from piccolo.columns import Column
from piccolo.migrations.auto.diffable_table import (
    DiffableTable,
    DropColumn,
)
from piccolo.migrations.auto.operations import RenameTable, RenameColumn
from piccolo.migrations.auto.migration_manager import MigrationManager


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
    def _rename_tables(self) -> t.List[RenameTable]:
        return list(
            chain(*[manager.rename_tables for manager in self.managers])
        )

    @property
    def remaining_tables(self) -> t.List[DiffableTable]:
        remaining: t.List[DiffableTable] = deepcopy(
            list(self._add_tables - self._drop_tables)
        )

        for renamed_table in self._rename_tables:
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
            i.new_class_name for i in self._rename_tables
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

        for renamed_table in self._rename_tables:
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
