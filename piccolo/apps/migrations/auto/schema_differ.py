from copy import deepcopy
from dataclasses import dataclass, field
from itertools import chain
import typing as t

from piccolo.apps.migrations.auto.diffable_table import (
    serialise_params,
    DiffableTable,
    TableDelta,
)
from piccolo.apps.migrations.auto.operations import RenameTable, RenameColumn
from piccolo.utils.printing import get_fixed_length_string


@dataclass
class RenameTableCollection:
    rename_tables: t.List[RenameTable] = field(default_factory=list)

    def append(self, renamed_table: RenameTable):
        self.rename_tables.append(renamed_table)

    @property
    def old_class_names(self):
        return [i.old_class_name for i in self.rename_tables]

    @property
    def new_class_names(self):
        return [i.new_class_name for i in self.rename_tables]

    def renamed_from(self, new_class_name: str) -> t.Optional[str]:
        """
        Returns the old class name, if it exists.
        """
        rename = [
            i for i in self.rename_tables if i.new_class_name == new_class_name
        ]
        if len(rename) > 0:
            return rename[0].old_class_name
        else:
            return None


@dataclass
class RenameColumnCollection:
    rename_columns: t.List[RenameColumn] = field(default_factory=list)

    def append(self, rename_column: RenameColumn):
        self.rename_columns.append(rename_column)

    def for_table_class_name(
        self, table_class_name: str
    ) -> t.List[RenameColumn]:
        return [
            i
            for i in self.rename_columns
            if i.table_class_name == table_class_name
        ]

    @property
    def old_column_names(self):
        return [i.old_column_name for i in self.rename_columns]

    @property
    def new_column_names(self):
        return [i.new_column_name for i in self.rename_columns]


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
        self.schema_snapshot_map: t.Dict[str, DiffableTable] = {
            i.class_name: i for i in self.schema_snapshot
        }
        self.rename_tables_collection = self.check_rename_tables()
        self.rename_columns_collection = self.check_renamed_columns()

    def check_rename_tables(self) -> RenameTableCollection:
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
        collection = RenameTableCollection()

        if len(drop_tables) == 0 or len(new_tables) == 0:
            # There needs to be at least one dropped table and one created
            # table for a rename to make sense.
            return collection

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
                        collection.append(
                            RenameTable(
                                old_class_name=drop_table.class_name,
                                old_tablename=drop_table.tablename,
                                new_class_name=new_table.class_name,
                                new_tablename=new_table.tablename,
                            )
                        )

        return collection

    def check_renamed_columns(self) -> RenameColumnCollection:
        """
        Work out whether any of the columns were renamed.
        """
        collection = RenameColumnCollection()

        for table in self.schema:
            snapshot_table = self.schema_snapshot_map.get(
                table.class_name, None
            )
            if not snapshot_table:
                continue
            delta: TableDelta = table - snapshot_table

            if (not delta.add_columns) and (not delta.drop_columns):
                continue

            # Detecting renamed columns is really tricky.
            # Even if a rename is detected, the column could also have changed
            # type. For now, each time a column is added and removed from a
            # table, ask if it's a rename.

            renamed_column_names: t.List[str] = []

            for add_column in delta.add_columns:
                if add_column.table_class_name in renamed_column_names:
                    continue

                for drop_column in delta.drop_columns:
                    user_response = (
                        self.auto_input
                        if self.auto_input
                        else input(
                            f"Did you rename the `{drop_column.column_name}` "
                            f"column to `{add_column.column_name}` on the "
                            f"`{ add_column.table_class_name }` table? (y/N)"
                        )
                    )
                    if user_response.lower() == "y":
                        renamed_column_names.append(
                            add_column.table_class_name
                        )
                        collection.append(
                            RenameColumn(
                                table_class_name=add_column.table_class_name,
                                tablename=drop_column.tablename,
                                old_column_name=drop_column.column_name,
                                new_column_name=add_column.column_name,
                            )
                        )

        return collection

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
            not in self.rename_tables_collection.new_class_names
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
            not in self.rename_tables_collection.old_class_names
        ]

        return [
            f"manager.drop_table(tablename='{i.tablename}')"
            for i in drop_tables
        ]

    @property
    def rename_tables(self) -> t.List[str]:
        return [
            f"manager.rename_table(old_class_name='{renamed_table.old_class_name}', old_tablename='{renamed_table.old_tablename}', new_class_name='{renamed_table.new_class_name}', new_tablename='{renamed_table.new_tablename}')"  # noqa
            for renamed_table in self.rename_tables_collection.rename_tables
        ]

    ###########################################################################

    def _get_snapshot_table(
        self, table_class_name: str
    ) -> t.Optional[DiffableTable]:
        snapshot_table = self.schema_snapshot_map.get(table_class_name, None)
        if snapshot_table:
            return snapshot_table
        else:
            if (
                table_class_name
                in self.rename_tables_collection.new_class_names
            ):
                class_name = self.rename_tables_collection.renamed_from(
                    table_class_name
                )
                snapshot_table = self.schema_snapshot_map.get(class_name)
                if snapshot_table:
                    snapshot_table.class_name = table_class_name
                    return snapshot_table
        return None

    @property
    def alter_columns(self) -> t.List[str]:
        response = []
        for table in self.schema:
            snapshot_table = self._get_snapshot_table(table.class_name)
            if snapshot_table:
                delta: TableDelta = table - snapshot_table
            else:
                continue

            for i in delta.alter_columns:
                response.append(
                    f"manager.alter_column(table_class_name='{table.class_name}', tablename='{table.tablename}', column_name='{i.column_name}', params={str(i.params)}, old_params={str(i.old_params)})"  # noqa
                )
        return response

    @property
    def drop_columns(self) -> t.List[str]:
        response = []
        for table in self.schema:
            snapshot_table = self._get_snapshot_table(table.class_name)
            if snapshot_table:
                delta: TableDelta = table - snapshot_table
            else:
                continue

            for column in delta.drop_columns:
                if (
                    column.column_name
                    in self.rename_columns_collection.old_column_names
                ):
                    continue

                response.append(
                    f"manager.drop_column(table_class_name='{table.class_name}', tablename='{table.tablename}', column_name='{column.column_name}')"  # noqa
                )
        return response

    @property
    def add_columns(self) -> t.List[str]:
        response = []
        for table in self.schema:
            snapshot_table = self._get_snapshot_table(table.class_name)
            if snapshot_table:
                delta: TableDelta = table - snapshot_table
            else:
                continue

            for column in delta.add_columns:
                if (
                    column.column_name
                    in self.rename_columns_collection.new_column_names
                ):
                    continue

                cleaned_params = serialise_params(column.params)

                response.append(
                    f"manager.add_column(table_class_name='{table.class_name}', tablename='{table.tablename}', column_name='{column.column_name}', column_class_name='{column.column_class_name}', params={str(cleaned_params)})"  # noqa
                )
        return response

    @property
    def rename_columns(self) -> t.List[str]:
        return [
            f"manager.rename_column(table_class_name='{i.table_class_name}', tablename='{i.tablename}', old_column_name='{i.old_column_name}', new_column_name='{i.new_column_name}')"  # noqa
            for i in self.rename_columns_collection.rename_columns
        ]

    ###########################################################################

    @property
    def new_table_columns(self) -> t.List[str]:
        new_tables: t.List[DiffableTable] = list(
            set(self.schema) - set(self.schema_snapshot)
        )

        response = []
        for table in new_tables:
            if (
                table.class_name
                in self.rename_tables_collection.new_class_names
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

    ###########################################################################

    def get_alter_statements(self) -> t.List[str]:
        """
        Call to execute the necessary alter commands on the database.
        """
        alter_statements: t.Dict[str, t.List[str]] = {
            "Created tables": self.create_tables,
            "Dropped tables": self.drop_tables,
            "Renamed tables": self.rename_tables,
            "Created table columns": self.new_table_columns,
            "Dropped columns": self.drop_columns,
            "Columns added to existing tables": self.add_columns,
            "Renamed columns": self.rename_columns,
            "Altered columns": self.alter_columns,
        }

        for message, statements in alter_statements.items():
            _message = get_fixed_length_string(message, length=40)
            count = len(statements)
            print(f"{_message} {count}")

        return list(chain(*alter_statements.values()))
