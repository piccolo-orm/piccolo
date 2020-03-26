from __future__ import annotations
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
import datetime
from enum import Enum
from inspect import isclass
from itertools import chain
import typing as t

from piccolo.columns import Column, OnDelete, OnUpdate
from piccolo.columns import column_types
from piccolo.custom_types import DatetimeDefault
from piccolo.engine import engine_finder
from piccolo.table import Table


@dataclass
class AlterColumn:
    table_class_name: str
    column_name: str
    tablename: str
    params: t.Dict[str, t.Any]


@dataclass
class DropColumn:
    table_class_name: str
    column_name: str
    tablename: str


@dataclass
class AddColumn:
    table_class_name: str
    column_name: str
    column_class_name: str
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


def serialise_params(params: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """
    When writing column params to a migration file, we need to serialise some
    of the values.
    """
    params = deepcopy(params)

    # We currently don't support defaults which are functions.
    default = params.get("default", None)
    if hasattr(default, "__call__"):
        raise ValueError(
            "Default arguments which are functions are not currently supported"
        )

    for key, value in params.items():
        # Convert enums into plain values
        if isinstance(value, Enum):
            params[key] = f"{value.__class__.__name__}.{value.name}"

        # Replace any Table class values into class names
        if isclass(value) and issubclass(value, Table):
            params[key] = value.__name__

        # Convert any datetime values into isoformat strings
        if isinstance(value, datetime.datetime):
            params[key] = value.isoformat()

    return params


def deserialise_params(params: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """
    When reading column params from a migration file, we need to convert them
    from their serialised form.
    """
    params = deepcopy(params)

    references = params.get("references")
    if references:
        _Table: t.Type[Table] = type(
            references, (Table,), {},
        )
        params["references"] = _Table

    on_delete = params.get("on_delete")
    if on_delete:
        enum_name, item_name = on_delete.split(".")
        if enum_name == "OnDelete":
            params["on_delete"] = getattr(OnDelete, item_name)

    on_update = params.get("on_update")
    if on_update:
        enum_name, item_name = on_update.split(".")
        if enum_name == "OnUpdate":
            params["on_update"] = getattr(OnUpdate, item_name)

    default = params.get("default")
    if isinstance(default, str):
        if default.startswith("DatetimeDefault"):
            _, item_name = default.split(".")
            params["default"] = getattr(DatetimeDefault, item_name)
        else:
            try:
                params["default"] = datetime.datetime.fromisoformat(default)
            except ValueError:
                pass

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
    previous_class_name: t.Optional[str] = None

    def __post_init__(self):
        self.columns_map: t.Dict[str, Column] = {
            i._meta.name: i for i in self.columns
        }

    def __sub__(self, value: DiffableTable) -> TableDelta:
        if not isinstance(value, DiffableTable):
            raise ValueError(
                "Can only diff with other DiffableTable instances"
            )

        if value.class_name != self.class_name:
            raise ValueError(
                "The two tables don't appear to have the same name."
            )

        add_columns = [
            AddColumn(
                table_class_name=self.class_name,
                column_name=i._meta.name,
                column_class_name=i.__class__.__name__,
                params=i._meta.params,
            )
            for i in (set(self.columns) - set(value.columns))
        ]

        drop_columns = [
            DropColumn(
                table_class_name=self.class_name,
                column_name=i._meta.name,
                tablename=value.tablename,
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
                serialise_params(existing_column._meta.params),
                serialise_params(column._meta.params),
            )
            if delta:
                alter_columns.append(
                    AlterColumn(
                        table_class_name=self.class_name,
                        tablename=self.tablename,
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
class RenamedTable:
    old_class_name: str
    new_class_name: str
    new_tablename: str


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


@dataclass
class AddColumnClass:
    column: Column
    table_class_name: str
    tablename: str


@dataclass
class AddColumnCollection:
    add_columns: t.List[AddColumnClass] = field(default_factory=list)

    def append(self, add_column: AddColumnClass):
        self.add_columns.append(add_column)

    def for_table_class_name(
        self, table_class_name: str
    ) -> t.List[AddColumnClass]:
        return [
            i
            for i in self.add_columns
            if i.table_class_name == table_class_name
        ]

    def columns_for_table_class_name(
        self, table_class_name: str
    ) -> t.List[Column]:
        return [
            i.column
            for i in self.add_columns
            if i.table_class_name == table_class_name
        ]

    @property
    def table_class_names(self) -> t.List[str]:
        return list(set([i.table_class_name for i in self.add_columns]))


@dataclass
class DropColumnCollection:
    drop_columns: t.List[DropColumn] = field(default_factory=list)

    def append(self, drop_column: DropColumn):
        self.drop_columns.append(drop_column)

    def for_table_class_name(self, table_class_name: str) -> t.List[str]:
        return [
            i.column_name
            for i in self.drop_columns
            if i.table_class_name == table_class_name
        ]

    @property
    def table_class_names(self) -> t.List[str]:
        return list(set([i.table_class_name for i in self.drop_columns]))


@dataclass
class RenameColumn:
    table_class_name: str
    tablename: str
    old_column_name: str
    new_column_name: str


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
    def table_class_names(self) -> t.List[str]:
        return list(set([i.table_class_name for i in self.rename_columns]))


@dataclass
class AlterColumnCollection:
    alter_columns: t.List[AlterColumn] = field(default_factory=list)

    def append(self, alter_column: AlterColumn):
        self.alter_columns.append(alter_column)

    def for_table_class_name(
        self, table_class_name: str
    ) -> t.List[AlterColumn]:
        return [
            i
            for i in self.alter_columns
            if i.table_class_name == table_class_name
        ]

    @property
    def table_class_names(self) -> t.List[str]:
        return list(set([i.column_name for i in self.alter_columns]))


@dataclass
class MigrationManager:
    """
    Each auto generated migration returns a MigrationManager. It contains
    all of the schema changes that migration wants to make.
    """

    migration_id: str = ""
    add_tables: t.List[DiffableTable] = field(default_factory=list)
    drop_tables: t.List[DiffableTable] = field(default_factory=list)
    rename_tables: t.List[RenamedTable] = field(default_factory=list)
    add_columns: AddColumnCollection = field(
        default_factory=AddColumnCollection
    )
    drop_columns: DropColumnCollection = field(
        default_factory=DropColumnCollection
    )
    rename_columns: RenameColumnCollection = field(
        default_factory=RenameColumnCollection
    )
    alter_columns: AlterColumnCollection = field(
        default_factory=AlterColumnCollection
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

    def rename_table(
        self, old_class_name: str, new_class_name: str, new_tablename: str
    ):
        self.rename_tables.append(
            RenamedTable(
                old_class_name=old_class_name,
                new_class_name=new_class_name,
                new_tablename=new_tablename,
            )
        )

    def add_column(
        self,
        table_class_name: str,
        tablename: str,
        column_name: str,
        column_class_name: str,
        params: t.Dict[str, t.Any] = {},
    ):
        column_class = getattr(column_types, column_class_name)
        cleaned_params = deserialise_params(params)
        column = column_class(**cleaned_params)
        column._meta.name = column_name
        self.add_columns.append(
            AddColumnClass(
                column=column,
                tablename=tablename,
                table_class_name=table_class_name,
            )
        )

    def drop_column(
        self, table_class_name: str, tablename: str, column_name: str
    ):
        self.drop_columns.append(
            DropColumn(
                table_class_name=table_class_name,
                column_name=column_name,
                tablename=tablename,
            )
        )

    def rename_column(
        self,
        table_class_name: str,
        tablename: str,
        old_column_name: str,
        new_column_name: str,
    ):
        self.rename_columns.append(
            RenameColumn(
                table_class_name=table_class_name,
                tablename=tablename,
                old_column_name=old_column_name,
                new_column_name=new_column_name,
            )
        )

    def alter_column(
        self,
        table_class_name: str,
        tablename: str,
        column_name: str,
        params: t.Dict[str, t.Any],
    ):
        """
        All possible alterations aren't currently supported.
        """
        self.alter_columns.append(
            AlterColumn(
                table_class_name=table_class_name,
                tablename=tablename,
                column_name=column_name,
                params=params,
            )
        )

    async def run(self):
        print("Running MigrationManager ...")

        engine = engine_finder()

        if not engine:
            raise Exception("Can't find engine")

        async with engine.transaction():

            # Add tables

            for table in self.add_tables:
                columns = self.add_columns.columns_for_table_class_name(
                    table.class_name
                )
                _Table: t.Type[Table] = type(
                    table.class_name,
                    (Table,),
                    {column._meta.name: column for column in columns},
                )
                _Table._meta.tablename = table.tablename

                await _Table.create_table().run()

            ###################################################################
            # Drop tables

            for table in self.drop_tables:
                _Table: t.Type[Table] = type(
                    table.class_name, (Table,), {},
                )
                await _Table.alter().drop_table().run()

            ###################################################################
            # Rename tables

            for rename_table in self.rename_tables:
                _Table: t.Type[Table] = type(
                    rename_table.old_class_name, (Table,), {}
                )
                await _Table.alter().rename_table(
                    new_name=rename_table.new_tablename
                ).run()

            ###################################################################
            # Add columns, which belong to existing tables

            new_table_class_names = [i.class_name for i in self.add_tables]

            for table_class_name in self.add_columns.table_class_names:
                if table_class_name in new_table_class_names:
                    continue

                add_columns: t.List[
                    AddColumnClass
                ] = self.add_columns.for_table_class_name(table_class_name)

                _Table: t.Type[Table] = type(
                    add_columns[0].table_class_name, (Table,), {}
                )
                _Table._meta.tablename = add_columns[0].tablename

                for add_column in add_columns:
                    column = add_column.column
                    await _Table.alter().add_column(
                        name=column._meta.name, column=column
                    ).run()

            ###################################################################
            # Drop columns

            for table_class_name in self.drop_columns.table_class_names:
                columns = self.drop_columns.for_table_class_name(
                    table_class_name
                )

                if not columns:
                    continue

                _Table: t.Type[Table] = type(table_class_name, (Table,), {})
                _Table._meta.tablename = columns[0].tablename

                for column in columns:
                    await _Table.alter().drop_column(
                        column=column.column_name
                    ).run()

            ###################################################################
            # Rename columns

            for table_class_name in self.rename_columns.table_class_names:
                columns = self.rename_columns.for_table_class_name(
                    table_class_name
                )

                if not columns:
                    continue

                _Table: t.Type[Table] = type(table_class_name, (Table,), {})
                _Table._meta.tablename = columns[0].tablename

                for column in columns:
                    await _Table.alter().rename_column(
                        column=column.old_column_name,
                        new_name=column.new_column_name,
                    ).run()

            ###################################################################
            # Alter columns

            for table_class_name in self.alter_columns.table_class_names:
                alter_columns = self.alter_columns.for_table_class_name(
                    table_class_name
                )

                if not alter_columns:
                    continue

                _Table: t.Type[Table] = type(table_class_name, (Table,), {})
                _Table._meta.tablename = alter_columns[0].tablename

                for column in alter_columns:
                    params = column.params
                    row_name = column.row_name

                    null = params.get("null")
                    if null is not None:
                        await _Table.alter().set_null(
                            column=row_name, boolean=null
                        ).run()

                    length = params.get("length")
                    if length is not None:
                        await _Table.alter().set_length(
                            column=row_name, length=length
                        ).run()

                    unique = params.get("unique")
                    if unique is not None:
                        await _Table.alter().set_unique(
                            column=row_name, boolean=unique
                        ).run()


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
