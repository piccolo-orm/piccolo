from __future__ import annotations

from dataclasses import dataclass, field

from piccolo.apps.migrations.auto.diffable_table import DiffableTable
from piccolo.apps.migrations.auto.migration_manager import MigrationManager


@dataclass
class SchemaSnapshot:
    """
    Adds up a sequence of MigrationManagers, and returns a snapshot of what
    the schema looks like.
    """

    # In ascending order of date created.
    managers: list[MigrationManager] = field(default_factory=list)

    ###########################################################################

    def get_table_from_snapshot(self, table_class_name: str) -> DiffableTable:
        snapshot = self.get_snapshot()
        filtered = [i for i in snapshot if i.class_name == table_class_name]
        if not filtered:
            raise ValueError(f"No match was found for {table_class_name}")
        return filtered[0]

    ###########################################################################

    def get_snapshot(self) -> list[DiffableTable]:
        tables: list[DiffableTable] = []

        sorted_managers = sorted(self.managers, key=lambda x: x.migration_id)

        for manager in sorted_managers:
            self._apply_add_tables(tables, manager)
            self._apply_drop_tables(tables, manager)
            self._apply_rename_tables(tables, manager)
            self._apply_change_table_schemas(tables, manager)

            for table in tables:
                self._apply_add_columns(table, manager)
                self._apply_drop_columns(table, manager)
                self._apply_alter_columns(table, manager)
                self._apply_rename_columns(table, manager)

        return tables

    ###########################################################################

    def _apply_add_tables(
        self, tables: list[DiffableTable], manager: MigrationManager
    ):
        for table in manager.add_tables:
            tables.append(table)

    def _apply_drop_tables(
        self, tables: list[DiffableTable], manager: MigrationManager
    ):
        for drop_table in manager.drop_tables:
            tables[:] = [
                i for i in tables if i.class_name != drop_table.class_name
            ]

    def _apply_rename_tables(
        self, tables: list[DiffableTable], manager: MigrationManager
    ):
        for rename_table in manager.rename_tables:
            for table in tables:
                if table.class_name == rename_table.old_class_name:
                    table.class_name = rename_table.new_class_name
                    table.tablename = rename_table.new_tablename
                    break

    def _apply_change_table_schemas(
        self, tables: list[DiffableTable], manager: MigrationManager
    ):
        for change_table_schema in manager.change_table_schemas:
            for table in tables:
                if table.tablename == change_table_schema.tablename:
                    table.schema = change_table_schema.new_schema
                    break

    def _apply_add_columns(
        self, table: DiffableTable, manager: MigrationManager
    ):
        add_columns = manager.add_columns.columns_for_table_class_name(
            table.class_name
        )
        table.columns.extend(add_columns)

    def _apply_drop_columns(
        self, table: DiffableTable, manager: MigrationManager
    ):
        drop_columns = manager.drop_columns.for_table_class_name(
            table.class_name
        )
        for drop_column in drop_columns:
            table.columns = [
                i
                for i in table.columns
                if i._meta.name != drop_column.column_name
            ]

    def _apply_alter_columns(
        self, table: DiffableTable, manager: MigrationManager
    ):
        alter_columns = manager.alter_columns.for_table_class_name(
            table.class_name
        )
        for alter_column in alter_columns:
            for index, column in enumerate(table.columns):
                if column._meta.name == alter_column.column_name:
                    for key, value in alter_column.params.items():
                        setattr(column._meta, key, value)
                        column._meta.params.update({key: value})
                    if (
                        alter_column.column_class
                        != alter_column.old_column_class
                    ) and alter_column.column_class is not None:
                        new_column = alter_column.column_class(
                            **column._meta.params
                        )
                        new_column._meta = column._meta
                        table.columns[index] = new_column

    def _apply_rename_columns(
        self, table: DiffableTable, manager: MigrationManager
    ):
        for rename_column in manager.rename_columns.for_table_class_name(
            table.class_name
        ):
            for column in table.columns:
                if column._meta.name == rename_column.old_column_name:
                    column._meta.name = rename_column.new_column_name
                    column._meta.db_column_name = (
                        rename_column.new_db_column_name
                    )
