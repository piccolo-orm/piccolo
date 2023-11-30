from __future__ import annotations

import inspect
import typing as t
from copy import deepcopy
from dataclasses import dataclass, field

from piccolo.apps.migrations.auto.diffable_table import (
    DiffableTable,
    TableDelta,
)
from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.apps.migrations.auto.operations import (
    ChangeTableSchema,
    RenameColumn,
    RenameTable,
)
from piccolo.apps.migrations.auto.serialisation import (
    Definition,
    Import,
    UniqueGlobalNames,
    serialise_params,
)
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

    def was_renamed_from(self, old_class_name: str) -> bool:
        """
        Returns ``True`` if the given class name was renamed.
        """
        for rename_table in self.rename_tables:
            if rename_table.old_class_name == old_class_name:
                return True
        return False

    def renamed_from(self, new_class_name: str) -> t.Optional[str]:
        """
        Returns the old class name, if it exists.
        """
        rename = [
            i for i in self.rename_tables if i.new_class_name == new_class_name
        ]
        return rename[0].old_class_name if rename else None


@dataclass
class ChangeTableSchemaCollection:
    collection: t.List[ChangeTableSchema] = field(default_factory=list)

    def append(self, change_table_schema: ChangeTableSchema):
        self.collection.append(change_table_schema)


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
class AlterStatements:
    statements: t.List[str] = field(default_factory=list)
    extra_imports: t.List[Import] = field(default_factory=list)
    extra_definitions: t.List[Definition] = field(default_factory=list)

    def extend(self, alter_statements: AlterStatements):
        self.statements.extend(alter_statements.statements)
        self.extra_imports.extend(alter_statements.extra_imports)
        self.extra_definitions.extend(alter_statements.extra_definitions)
        return self


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

    def __post_init__(self) -> None:
        self.schema_snapshot_map: t.Dict[str, DiffableTable] = {
            i.class_name: i for i in self.schema_snapshot
        }
        self.table_schema_changes_collection = (
            self.check_table_schema_changes()
        )
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
            new_column_names = [
                i._meta.db_column_name for i in new_table.columns
            ]
            for drop_table in drop_tables:
                if collection.was_renamed_from(
                    old_class_name=drop_table.class_name
                ):
                    # We've already detected a table that was renamed from
                    # this, so we can continue.
                    # This can happen if we're renaming lots of tables in a
                    # single migration.
                    # https://github.com/piccolo-orm/piccolo/discussions/832
                    continue

                drop_column_names = [
                    i._meta.db_column_name for i in new_table.columns
                ]
                same_column_names = set(new_column_names).intersection(
                    drop_column_names
                )
                if len(same_column_names) > 0:
                    if (
                        drop_table.class_name == new_table.class_name
                        and drop_table.tablename != new_table.tablename
                    ):
                        # The class names are the same, but the tablename
                        # has changed - we can assume this is a deliberate
                        # rename.
                        collection.append(
                            RenameTable(
                                old_class_name=drop_table.class_name,
                                old_tablename=drop_table.tablename,
                                new_class_name=new_table.class_name,
                                new_tablename=new_table.tablename,
                                schema=new_table.schema,
                            )
                        )
                        break

                    user_response = (
                        self.auto_input
                        if self.auto_input
                        else input(
                            f"Did you rename {drop_table.class_name} "
                            f"(tablename: {drop_table.tablename}) to "
                            f"{new_table.class_name} "
                            f"(tablename: {new_table.tablename})? (y/N)"
                        )
                    )
                    if user_response.lower() == "y":
                        collection.append(
                            RenameTable(
                                old_class_name=drop_table.class_name,
                                old_tablename=drop_table.tablename,
                                new_class_name=new_table.class_name,
                                new_tablename=new_table.tablename,
                                schema=new_table.schema,
                            )
                        )
                        break

        return collection

    def check_table_schema_changes(self) -> ChangeTableSchemaCollection:
        collection = ChangeTableSchemaCollection()

        for table in self.schema:
            snapshot_table = self.schema_snapshot_map.get(
                table.class_name, None
            )
            if not snapshot_table:
                continue

            if table.schema != snapshot_table.schema:
                collection.append(
                    ChangeTableSchema(
                        class_name=table.class_name,
                        tablename=table.tablename,
                        new_schema=table.schema,
                        old_schema=snapshot_table.schema,
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

            # We track which dropped columns have already been identified by
            # the user as renames, so we don't ask them if another column
            # was also renamed from it.
            used_drop_column_names: t.List[str] = []

            for add_column in delta.add_columns:
                for drop_column in delta.drop_columns:
                    if drop_column.column_name in used_drop_column_names:
                        continue

                    user_response = self.auto_input or input(
                        f"Did you rename the `{drop_column.db_column_name}` "  # noqa: E501
                        f"column to `{add_column.db_column_name}` on the "
                        f"`{add_column.table_class_name}` table? (y/N)"
                    )
                    if user_response.lower() == "y":
                        used_drop_column_names.append(drop_column.column_name)
                        collection.append(
                            RenameColumn(
                                table_class_name=add_column.table_class_name,
                                tablename=drop_column.tablename,
                                old_column_name=drop_column.column_name,
                                new_column_name=add_column.column_name,
                                old_db_column_name=drop_column.db_column_name,
                                new_db_column_name=add_column.db_column_name,
                                schema=add_column.schema,
                            )
                        )
                        break

        return collection

    ###########################################################################

    def _stringify_func(
        self,
        func: t.Callable,
        params: t.Dict[str, t.Any],
        prefix: t.Optional[str] = None,
    ) -> AlterStatements:
        """
        Generates a string representing how to call the given function with the
        give params. For example::

            def my_callable(arg_1: str, arg_2: str):
                ...

            >>> _stringify_func(
            ...     my_callable,
            ...     {"arg_1": "a", "arg_2": "b"}
            ... ).statements
            ['my_callable(arg_1="a", arg_2="b")']

        """
        signature = inspect.signature(func)

        if "self" in signature.parameters.keys():
            params["self"] = None

        serialised_params = serialise_params(params)

        func_name = func.__name__

        # This will raise an exception is we're missing parameters, which helps
        # with debugging:
        bound = signature.bind(**serialised_params.params)
        bound.apply_defaults()

        args = bound.arguments
        if "self" in args:
            args.pop("self")

        args_str = ", ".join(f"{i}={repr(j)}" for i, j in args.items())

        return AlterStatements(
            statements=[f"{prefix or ''}{func_name}({args_str})"],
            extra_definitions=serialised_params.extra_definitions,
            extra_imports=serialised_params.extra_imports,
        )

    ###########################################################################

    @property
    def create_tables(self) -> AlterStatements:
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

        alter_statements = AlterStatements()

        for i in new_tables:
            alter_statements.extend(
                self._stringify_func(
                    func=MigrationManager.add_table,
                    params={
                        "class_name": i.class_name,
                        "tablename": i.tablename,
                        "schema": i.schema,
                    },
                    prefix="manager.",
                )
            )

        return alter_statements

    @property
    def drop_tables(self) -> AlterStatements:
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

        alter_statements = AlterStatements()

        for i in drop_tables:
            alter_statements.extend(
                self._stringify_func(
                    func=MigrationManager.drop_table,
                    params={
                        "class_name": i.class_name,
                        "tablename": i.tablename,
                        "schema": i.schema,
                    },
                    prefix="manager.",
                )
            )

        return alter_statements

    @property
    def rename_tables(self) -> AlterStatements:
        alter_statements = AlterStatements()

        for i in self.rename_tables_collection.rename_tables:
            alter_statements.extend(
                self._stringify_func(
                    func=MigrationManager.rename_table,
                    params=i.__dict__,
                    prefix="manager.",
                )
            )

        return alter_statements

    @property
    def change_table_schemas(self) -> AlterStatements:
        alter_statements = AlterStatements()

        for i in self.table_schema_changes_collection.collection:
            alter_statements.extend(
                self._stringify_func(
                    func=MigrationManager.change_table_schema,
                    params=i.__dict__,
                    prefix="manager.",
                )
            )

        return alter_statements

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
                if class_name:
                    snapshot_table = self.schema_snapshot_map.get(class_name)
                    if snapshot_table:
                        snapshot_table.class_name = table_class_name
                        return snapshot_table
        return None

    @property
    def alter_columns(self) -> AlterStatements:
        response: t.List[str] = []
        extra_imports: t.List[Import] = []
        extra_definitions: t.List[Definition] = []
        for table in self.schema:
            snapshot_table = self._get_snapshot_table(table.class_name)
            if snapshot_table:
                delta: TableDelta = table - snapshot_table
            else:
                continue

            for alter_column in delta.alter_columns:
                new_params = serialise_params(alter_column.params)
                extra_imports.extend(new_params.extra_imports)
                extra_definitions.extend(new_params.extra_definitions)

                old_params = serialise_params(alter_column.old_params)
                extra_imports.extend(old_params.extra_imports)
                extra_definitions.extend(old_params.extra_definitions)

                column_class = (
                    alter_column.column_class.__name__
                    if alter_column.column_class
                    else "None"
                )

                old_column_class = (
                    alter_column.old_column_class.__name__
                    if alter_column.old_column_class
                    else "None"
                )

                if alter_column.column_class is not None:
                    extra_imports.append(
                        Import(
                            module=alter_column.column_class.__module__,
                            target=alter_column.column_class.__name__,
                            expect_conflict_with_global_name=getattr(
                                UniqueGlobalNames,
                                f"COLUMN_{alter_column.column_class.__name__.upper()}",  # noqa: E501
                                None,
                            ),
                        )
                    )

                if alter_column.old_column_class is not None:
                    extra_imports.append(
                        Import(
                            module=alter_column.old_column_class.__module__,
                            target=alter_column.old_column_class.__name__,
                            expect_conflict_with_global_name=getattr(
                                UniqueGlobalNames,
                                f"COLUMN_{alter_column.old_column_class.__name__.upper()}",  # noqa: E501
                            ),
                        )
                    )

                schema_str = (
                    "None"
                    if alter_column.schema is None
                    else f'"{alter_column.schema}"'
                )

                response.append(
                    f"manager.alter_column(table_class_name='{table.class_name}', tablename='{table.tablename}', column_name='{alter_column.column_name}', db_column_name='{alter_column.db_column_name}', params={new_params.params}, old_params={old_params.params}, column_class={column_class}, old_column_class={old_column_class}, schema={schema_str})"  # noqa: E501
                )

        return AlterStatements(
            statements=response,
            extra_imports=extra_imports,
            extra_definitions=extra_definitions,
        )

    @property
    def drop_columns(self) -> AlterStatements:
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

                schema_str = (
                    "None" if column.schema is None else f'"{column.schema}"'
                )

                response.append(
                    f"manager.drop_column(table_class_name='{table.class_name}', tablename='{table.tablename}', column_name='{column.column_name}', db_column_name='{column.db_column_name}', schema={schema_str})"  # noqa: E501
                )
        return AlterStatements(statements=response)

    @property
    def add_columns(self) -> AlterStatements:
        response: t.List[str] = []
        extra_imports: t.List[Import] = []
        extra_definitions: t.List[Definition] = []
        for table in self.schema:
            snapshot_table = self._get_snapshot_table(table.class_name)
            if snapshot_table:
                delta: TableDelta = table - snapshot_table
            else:
                continue

            for add_column in delta.add_columns:
                if (
                    add_column.column_name
                    in self.rename_columns_collection.new_column_names
                ):
                    continue

                params = serialise_params(add_column.params)
                cleaned_params = params.params
                extra_imports.extend(params.extra_imports)
                extra_definitions.extend(params.extra_definitions)

                column_class = add_column.column_class
                extra_imports.append(
                    Import(
                        module=column_class.__module__,
                        target=column_class.__name__,
                        expect_conflict_with_global_name=getattr(
                            UniqueGlobalNames,
                            f"COLUMN_{column_class.__name__.upper()}",
                            None,
                        ),
                    )
                )

                schema_str = (
                    "None"
                    if add_column.schema is None
                    else f'"{add_column.schema}"'
                )

                response.append(
                    f"manager.add_column(table_class_name='{table.class_name}', tablename='{table.tablename}', column_name='{add_column.column_name}', db_column_name='{add_column.db_column_name}', column_class_name='{add_column.column_class_name}', column_class={column_class.__name__}, params={str(cleaned_params)}, schema={schema_str})"  # noqa: E501
                )
        return AlterStatements(
            statements=response,
            extra_imports=extra_imports,
            extra_definitions=extra_definitions,
        )

    @property
    def rename_columns(self) -> AlterStatements:
        alter_statements = AlterStatements()

        for i in self.rename_columns_collection.rename_columns:
            alter_statements.extend(
                self._stringify_func(
                    func=MigrationManager.rename_column,
                    params=i.__dict__,
                    prefix="manager.",
                )
            )

        return alter_statements

    ###########################################################################

    @property
    def new_table_columns(self) -> AlterStatements:
        new_tables: t.List[DiffableTable] = list(
            set(self.schema) - set(self.schema_snapshot)
        )

        response: t.List[str] = []
        extra_imports: t.List[Import] = []
        extra_definitions: t.List[Definition] = []
        for table in new_tables:
            if (
                table.class_name
                in self.rename_tables_collection.new_class_names
            ):
                continue

            for column in table.columns:
                # In case we cause subtle bugs:
                params = deepcopy(column._meta.params)
                _params = serialise_params(params)
                cleaned_params = _params.params
                extra_imports.extend(_params.extra_imports)
                extra_definitions.extend(_params.extra_definitions)

                extra_imports.append(
                    Import(
                        module=column.__class__.__module__,
                        target=column.__class__.__name__,
                        expect_conflict_with_global_name=getattr(
                            UniqueGlobalNames,
                            f"COLUMN_{column.__class__.__name__.upper()}",
                            None,
                        ),
                    )
                )

                schema_str = (
                    "None" if table.schema is None else f'"{table.schema}"'
                )

                response.append(
                    f"manager.add_column(table_class_name='{table.class_name}', tablename='{table.tablename}', column_name='{column._meta.name}', db_column_name='{column._meta.db_column_name}', column_class_name='{column.__class__.__name__}', column_class={column.__class__.__name__}, params={str(cleaned_params)}, schema={schema_str})"  # noqa: E501
                )
        return AlterStatements(
            statements=response,
            extra_imports=extra_imports,
            extra_definitions=extra_definitions,
        )

    ###########################################################################

    def get_alter_statements(self) -> t.List[AlterStatements]:
        """
        Call to execute the necessary alter commands on the database.
        """
        alter_statements: t.Dict[str, AlterStatements] = {
            "Created tables": self.create_tables,
            "Dropped tables": self.drop_tables,
            "Renamed tables": self.rename_tables,
            "Tables which changed schema": self.change_table_schemas,
            "Created table columns": self.new_table_columns,
            "Dropped columns": self.drop_columns,
            "Columns added to existing tables": self.add_columns,
            "Renamed columns": self.rename_columns,
            "Altered columns": self.alter_columns,
        }

        for message, statements in alter_statements.items():
            _message = get_fixed_length_string(message, length=40)
            count = len(statements.statements)
            print(f"{_message} {count}")

        return list(alter_statements.values())
