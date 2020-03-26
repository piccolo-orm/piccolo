from copy import deepcopy
from dataclasses import dataclass, field
from itertools import chain
import typing as t

from piccolo.migrations.auto.diffable_table import (
    serialise_params,
    DiffableTable,
    TableDelta,
)
from piccolo.migrations.auto.operations import RenameTable


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
        self.rename_tables_collection = self.check_rename_tables()

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
        rename_tables_collection = RenameTableCollection()

        if len(drop_tables) == 0 or len(new_tables) == 0:
            # There needs to be at least one dropped table and one created
            # table for a rename to make sense.
            return rename_tables_collection

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
                        rename_tables_collection.append(
                            RenameTable(
                                old_class_name=drop_table.class_name,
                                new_class_name=new_table.class_name,
                                new_tablename=new_table.tablename,
                            )
                        )

        return rename_tables_collection

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
            f"manager.rename_table(old_class_name='{renamed_table.old_class_name}', new_class_name='{renamed_table.new_class_name}', new_tablename='{renamed_table.new_tablename}')"  # noqa
            for renamed_table in self.rename_tables_collection.rename_tables
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
