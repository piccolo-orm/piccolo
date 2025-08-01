from __future__ import annotations

import inspect
import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import Any, Optional, Union

from piccolo.apps.migrations.auto.diffable_table import DiffableTable
from piccolo.apps.migrations.auto.operations import (
    AlterColumn,
    ChangeTableSchema,
    DropColumn,
    RenameColumn,
    RenameTable,
)
from piccolo.apps.migrations.auto.serialisation import deserialise_params
from piccolo.columns import Column, column_types
from piccolo.columns.column_types import ForeignKey, Serial
from piccolo.engine import engine_finder
from piccolo.query import Query
from piccolo.query.base import DDL
from piccolo.query.constraints import get_fk_constraint_name
from piccolo.schema import SchemaDDLBase
from piccolo.table import Table, create_table_class, sort_table_classes
from piccolo.utils.warnings import colored_warning

logger = logging.getLogger(__name__)


@dataclass
class AddColumnClass:
    column: Column
    table_class_name: str
    tablename: str
    schema: Optional[str]


@dataclass
class AddColumnCollection:
    add_columns: list[AddColumnClass] = field(default_factory=list)

    def append(self, add_column: AddColumnClass):
        self.add_columns.append(add_column)

    def for_table_class_name(
        self, table_class_name: str
    ) -> list[AddColumnClass]:
        return [
            i
            for i in self.add_columns
            if i.table_class_name == table_class_name
        ]

    def columns_for_table_class_name(
        self, table_class_name: str
    ) -> list[Column]:
        return [
            i.column
            for i in self.add_columns
            if i.table_class_name == table_class_name
        ]

    @property
    def table_class_names(self) -> list[str]:
        return list({i.table_class_name for i in self.add_columns})


@dataclass
class DropColumnCollection:
    drop_columns: list[DropColumn] = field(default_factory=list)

    def append(self, drop_column: DropColumn):
        self.drop_columns.append(drop_column)

    def for_table_class_name(self, table_class_name: str) -> list[DropColumn]:
        return [
            i
            for i in self.drop_columns
            if i.table_class_name == table_class_name
        ]

    @property
    def table_class_names(self) -> list[str]:
        return list({i.table_class_name for i in self.drop_columns})


@dataclass
class RenameColumnCollection:
    rename_columns: list[RenameColumn] = field(default_factory=list)

    def append(self, rename_column: RenameColumn):
        self.rename_columns.append(rename_column)

    def for_table_class_name(
        self, table_class_name: str
    ) -> list[RenameColumn]:
        return [
            i
            for i in self.rename_columns
            if i.table_class_name == table_class_name
        ]

    @property
    def table_class_names(self) -> list[str]:
        return list({i.table_class_name for i in self.rename_columns})


@dataclass
class AlterColumnCollection:
    alter_columns: list[AlterColumn] = field(default_factory=list)

    def append(self, alter_column: AlterColumn):
        self.alter_columns.append(alter_column)

    def for_table_class_name(self, table_class_name: str) -> list[AlterColumn]:
        return [
            i
            for i in self.alter_columns
            if i.table_class_name == table_class_name
        ]

    @property
    def table_class_names(self) -> list[str]:
        return list({i.table_class_name for i in self.alter_columns})


AsyncFunction = Callable[[], Coroutine]


class SkippedTransaction:
    async def __aenter__(self):
        print("Automatic transaction disabled")

    async def __aexit__(self, *args, **kwargs):
        pass


@dataclass
class MigrationManager:
    """
    Each auto generated migration returns a MigrationManager. It contains
    all of the schema changes that migration wants to make.

    :param wrap_in_transaction:
        By default, the migration is wrapped in a transaction, so if anything
        fails, the whole migration will get rolled back. You can disable this
        behaviour if you want - for example, in a manual migration you might
        want to create the transaction yourself (perhaps you're using
        savepoints), or you may want multiple transactions.

    """

    migration_id: str = ""
    app_name: str = ""
    description: str = ""
    preview: bool = False
    add_tables: list[DiffableTable] = field(default_factory=list)
    drop_tables: list[DiffableTable] = field(default_factory=list)
    rename_tables: list[RenameTable] = field(default_factory=list)
    change_table_schemas: list[ChangeTableSchema] = field(default_factory=list)
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
    raw: list[Union[Callable, AsyncFunction]] = field(default_factory=list)
    raw_backwards: list[Union[Callable, AsyncFunction]] = field(
        default_factory=list
    )
    fake: bool = False
    wrap_in_transaction: bool = True

    def add_table(
        self,
        class_name: str,
        tablename: str,
        schema: Optional[str] = None,
        columns: Optional[list[Column]] = None,
    ):
        if not columns:
            columns = []

        self.add_tables.append(
            DiffableTable(
                class_name=class_name,
                tablename=tablename,
                columns=columns,
                schema=schema,
            )
        )

    def drop_table(
        self, class_name: str, tablename: str, schema: Optional[str] = None
    ):
        self.drop_tables.append(
            DiffableTable(
                class_name=class_name, tablename=tablename, schema=schema
            )
        )

    def change_table_schema(
        self,
        class_name: str,
        tablename: str,
        new_schema: Optional[str] = None,
        old_schema: Optional[str] = None,
    ):
        self.change_table_schemas.append(
            ChangeTableSchema(
                class_name=class_name,
                tablename=tablename,
                new_schema=new_schema,
                old_schema=old_schema,
            )
        )

    def rename_table(
        self,
        old_class_name: str,
        old_tablename: str,
        new_class_name: str,
        new_tablename: str,
        schema: Optional[str] = None,
    ):
        self.rename_tables.append(
            RenameTable(
                old_class_name=old_class_name,
                old_tablename=old_tablename,
                new_class_name=new_class_name,
                new_tablename=new_tablename,
                schema=schema,
            )
        )

    def add_column(
        self,
        table_class_name: str,
        tablename: str,
        column_name: str,
        db_column_name: Optional[str] = None,
        column_class_name: str = "",
        column_class: Optional[type[Column]] = None,
        params: Optional[dict[str, Any]] = None,
        schema: Optional[str] = None,
    ):
        """
        Add a new column to the table.

        :param column_class_name:
            The column type was traditionally specified as a string, using this
            variable. This didn't allow users to define custom column types
            though, which is why newer migrations directly reference a
            ``Column`` subclass using ``column_class``.
        :param column_class:
            A direct reference to a ``Column`` subclass.

        """
        if params is None:
            params = {}
        column_class = column_class or getattr(column_types, column_class_name)

        if column_class is None:
            raise ValueError("Unrecognised column type")

        cleaned_params = deserialise_params(params=params)
        column = column_class(**cleaned_params)
        column._meta.name = column_name
        if db_column_name:
            column._meta.db_column_name = db_column_name

        self.add_columns.append(
            AddColumnClass(
                column=column,
                tablename=tablename,
                table_class_name=table_class_name,
                schema=schema,
            )
        )

    def drop_column(
        self,
        table_class_name: str,
        tablename: str,
        column_name: str,
        db_column_name: Optional[str] = None,
        schema: Optional[str] = None,
    ):
        self.drop_columns.append(
            DropColumn(
                table_class_name=table_class_name,
                column_name=column_name,
                db_column_name=db_column_name or column_name,
                tablename=tablename,
                schema=schema,
            )
        )

    def rename_column(
        self,
        table_class_name: str,
        tablename: str,
        old_column_name: str,
        new_column_name: str,
        old_db_column_name: Optional[str] = None,
        new_db_column_name: Optional[str] = None,
        schema: Optional[str] = None,
    ):
        self.rename_columns.append(
            RenameColumn(
                table_class_name=table_class_name,
                tablename=tablename,
                old_column_name=old_column_name,
                new_column_name=new_column_name,
                old_db_column_name=old_db_column_name or old_column_name,
                new_db_column_name=new_db_column_name or new_column_name,
                schema=schema,
            )
        )

    def alter_column(
        self,
        table_class_name: str,
        tablename: str,
        column_name: str,
        db_column_name: Optional[str] = None,
        params: Optional[dict[str, Any]] = None,
        old_params: Optional[dict[str, Any]] = None,
        column_class: Optional[type[Column]] = None,
        old_column_class: Optional[type[Column]] = None,
        schema: Optional[str] = None,
    ):
        """
        All possible alterations aren't currently supported.
        """
        if params is None:
            params = {}
        if old_params is None:
            old_params = {}
        self.alter_columns.append(
            AlterColumn(
                table_class_name=table_class_name,
                tablename=tablename,
                column_name=column_name,
                db_column_name=db_column_name or column_name,
                params=params,
                old_params=old_params,
                column_class=column_class,
                old_column_class=old_column_class,
                schema=schema,
            )
        )

    def add_raw(self, raw: Union[Callable, AsyncFunction]):
        """
        A migration manager can execute arbitrary functions or coroutines when
        run. This is useful if you want to execute raw SQL.
        """
        self.raw.append(raw)

    def add_raw_backwards(self, raw: Union[Callable, AsyncFunction]):
        """
        When reversing a migration, you may want to run extra code to help
        clean up.
        """
        self.raw_backwards.append(raw)

    ###########################################################################

    async def get_table_from_snapshot(
        self,
        table_class_name: str,
        app_name: Optional[str],
        offset: int = 0,
        migration_id: Optional[str] = None,
    ) -> type[Table]:
        """
        Returns a Table subclass which can be used for modifying data within
        a migration.

        :param offset:
            Lets you get a table as it appeared in an older migration. If the
            offset is -1, the table will come from the previous migration.

        """
        from piccolo.apps.migrations.commands.base import BaseMigrationManager

        if migration_id is None:
            migration_id = self.migration_id

        if app_name is None:
            app_name = self.app_name

        diffable_table = await BaseMigrationManager().get_table_from_snapshot(
            app_name=app_name,
            table_class_name=table_class_name,
            max_migration_id=migration_id,
            offset=offset,
        )
        return diffable_table.to_table_class()

    ###########################################################################

    @staticmethod
    async def _print_query(query: Union[DDL, Query, SchemaDDLBase]):
        if isinstance(query, DDL):
            print("\n", ";".join(query.ddl) + ";")
        else:
            print(str(query))

    async def _run_query(self, query: Union[DDL, Query, SchemaDDLBase]):
        """
        If MigrationManager is in preview mode then it just print the query
        instead of executing it.
        """
        if self.preview:
            await self._print_query(query)
        else:
            await query.run()

    async def _run_alter_columns(self, backwards: bool = False):
        for table_class_name in self.alter_columns.table_class_names:
            alter_columns = self.alter_columns.for_table_class_name(
                table_class_name
            )

            if not alter_columns:
                continue

            _Table: type[Table] = create_table_class(
                class_name=table_class_name,
                class_kwargs={
                    "tablename": alter_columns[0].tablename,
                    "schema": alter_columns[0].schema,
                },
            )

            for alter_column in alter_columns:
                params = (
                    alter_column.old_params
                    if backwards
                    else alter_column.params
                )

                old_params = (
                    alter_column.params
                    if backwards
                    else alter_column.old_params
                )

                ###############################################################

                # Change the column type if possible
                column_class = (
                    alter_column.old_column_class
                    if backwards
                    else alter_column.column_class
                )
                old_column_class = (
                    alter_column.column_class
                    if backwards
                    else alter_column.old_column_class
                )

                if (old_column_class is not None) and (
                    column_class is not None
                ):
                    if old_column_class != column_class:
                        old_column = old_column_class(**old_params)
                        old_column._meta._table = _Table
                        old_column._meta._name = alter_column.column_name
                        old_column._meta.db_column_name = (
                            alter_column.db_column_name
                        )

                        new_column = column_class(**params)
                        new_column._meta._table = _Table
                        new_column._meta._name = alter_column.column_name
                        new_column._meta.db_column_name = (
                            alter_column.db_column_name
                        )

                        using_expression: Optional[str] = None

                        # Postgres won't automatically cast some types to
                        # others. We may as well try, as it will definitely
                        # fail otherwise.
                        if new_column.value_type != old_column.value_type:
                            if old_params.get("default", ...) is not None:
                                # Unless the column's default value is also
                                # something which can be cast to the new type,
                                # it will also fail. Drop the default value for
                                # now - the proper default is set later on.
                                await self._run_query(
                                    _Table.alter().drop_default(old_column)
                                )

                            using_expression = "{}::{}".format(
                                alter_column.db_column_name,
                                new_column.column_type,
                            )

                        # We can't migrate a SERIAL to a BIGSERIAL or vice
                        # versa, as SERIAL isn't a true type, just an alias to
                        # other commands.
                        if issubclass(column_class, Serial) and issubclass(
                            old_column_class, Serial
                        ):
                            colored_warning(
                                "Unable to migrate Serial to BigSerial and "
                                "vice versa. This must be done manually."
                            )
                        else:
                            await self._run_query(
                                _Table.alter().set_column_type(
                                    old_column=old_column,
                                    new_column=new_column,
                                    using_expression=using_expression,
                                )
                            )

                ###############################################################

                on_delete = params.get("on_delete")
                on_update = params.get("on_update")
                if on_delete is not None or on_update is not None:
                    existing_table = await self.get_table_from_snapshot(
                        table_class_name=table_class_name,
                        app_name=self.app_name,
                    )

                    fk_column = existing_table._meta.get_column_by_name(
                        alter_column.column_name
                    )

                    assert isinstance(fk_column, ForeignKey)

                    # First drop the existing foreign key constraint
                    constraint_name = await get_fk_constraint_name(
                        column=fk_column
                    )
                    await self._run_query(
                        _Table.alter().drop_constraint(
                            constraint_name=constraint_name
                        )
                    )

                    # Then add a new foreign key constraint
                    await self._run_query(
                        _Table.alter().add_foreign_key_constraint(
                            column=fk_column,
                            on_delete=on_delete,
                            on_update=on_update,
                        )
                    )

                null = params.get("null")
                if null is not None:
                    await self._run_query(
                        _Table.alter().set_null(
                            column=alter_column.db_column_name, boolean=null
                        )
                    )

                length = params.get("length")
                if length is not None:
                    await self._run_query(
                        _Table.alter().set_length(
                            column=alter_column.db_column_name, length=length
                        )
                    )

                unique = params.get("unique")
                if unique is not None:
                    # When modifying unique constraints, we need to pass in
                    # a column type, and not just the column name.
                    column = Column()
                    column._meta._table = _Table
                    column._meta._name = alter_column.column_name
                    column._meta.db_column_name = alter_column.db_column_name
                    await self._run_query(
                        _Table.alter().set_unique(
                            column=column, boolean=unique
                        )
                    )

                index = params.get("index")
                index_method = params.get("index_method")
                if index is None:
                    if index_method is not None:
                        # If the index value hasn't changed, but the
                        # index_method value has, this indicates we need
                        # to change the index type.
                        column = Column()
                        column._meta._table = _Table
                        column._meta._name = alter_column.column_name
                        column._meta.db_column_name = (
                            alter_column.db_column_name
                        )
                        await self._run_query(_Table.drop_index([column]))
                        await self._run_query(
                            _Table.create_index(
                                [column],
                                method=index_method,
                                if_not_exists=True,
                            )
                        )
                else:
                    # If the index value has changed, then we are either
                    # dropping, or creating an index.
                    column = Column()
                    column._meta._table = _Table
                    column._meta._name = alter_column.column_name
                    column._meta.db_column_name = alter_column.db_column_name

                    if index is True:
                        kwargs = (
                            {"method": index_method} if index_method else {}
                        )
                        await self._run_query(
                            _Table.create_index(
                                [column], if_not_exists=True, **kwargs
                            )
                        )
                    else:
                        await self._run_query(_Table.drop_index([column]))

                # None is a valid value, so retrieve ellipsis if not found.
                default = params.get("default", ...)
                if default is not ...:
                    column = Column()
                    column._meta._table = _Table
                    column._meta._name = alter_column.column_name
                    column._meta.db_column_name = alter_column.db_column_name

                    if default is None:
                        await self._run_query(
                            _Table.alter().drop_default(column=column)
                        )
                    else:
                        column.default = default
                        await self._run_query(
                            _Table.alter().set_default(
                                column=column, value=column.get_default_value()
                            )
                        )

                # None is a valid value, so retrieve ellipsis if not found.
                digits = params.get("digits", ...)
                if digits is not ...:
                    await self._run_query(
                        _Table.alter().set_digits(
                            column=alter_column.db_column_name,
                            digits=digits,
                        )
                    )

    async def _run_drop_tables(self, backwards=False):
        for diffable_table in self.drop_tables:
            if backwards:
                _Table = await self.get_table_from_snapshot(
                    table_class_name=diffable_table.class_name,
                    app_name=self.app_name,
                    offset=-1,
                )
                await self._run_query(_Table.create_table())
            else:
                await self._run_query(
                    diffable_table.to_table_class().alter().drop_table()
                )

    async def _run_drop_columns(self, backwards: bool = False):
        if backwards:
            for drop_column in self.drop_columns.drop_columns:
                _Table = await self.get_table_from_snapshot(
                    table_class_name=drop_column.table_class_name,
                    app_name=self.app_name,
                    offset=-1,
                )
                column_to_restore = _Table._meta.get_column_by_name(
                    drop_column.column_name
                )
                await self._run_query(
                    _Table.alter().add_column(
                        name=drop_column.column_name, column=column_to_restore
                    )
                )
        else:
            for table_class_name in self.drop_columns.table_class_names:
                columns = self.drop_columns.for_table_class_name(
                    table_class_name
                )

                if not columns:
                    continue

                _Table = create_table_class(
                    class_name=table_class_name,
                    class_kwargs={
                        "tablename": columns[0].tablename,
                        "schema": columns[0].schema,
                    },
                )

                for column in columns:
                    await self._run_query(
                        _Table.alter().drop_column(column=column.column_name)
                    )

    async def _run_rename_tables(self, backwards: bool = False):
        for rename_table in self.rename_tables:
            class_name = (
                rename_table.new_class_name
                if backwards
                else rename_table.old_class_name
            )
            tablename = (
                rename_table.new_tablename
                if backwards
                else rename_table.old_tablename
            )
            new_tablename = (
                rename_table.old_tablename
                if backwards
                else rename_table.new_tablename
            )

            _Table: type[Table] = create_table_class(
                class_name=class_name,
                class_kwargs={
                    "tablename": tablename,
                    "schema": rename_table.schema,
                },
            )

            await self._run_query(
                _Table.alter().rename_table(new_name=new_tablename)
            )

    async def _run_rename_columns(self, backwards: bool = False):
        for table_class_name in self.rename_columns.table_class_names:
            columns = self.rename_columns.for_table_class_name(
                table_class_name
            )

            if not columns:
                continue

            _Table: type[Table] = create_table_class(
                class_name=table_class_name,
                class_kwargs={
                    "tablename": columns[0].tablename,
                    "schema": columns[0].schema,
                },
            )

            for rename_column in columns:
                column = (
                    rename_column.new_db_column_name
                    if backwards
                    else rename_column.old_db_column_name
                )
                new_name = (
                    rename_column.old_db_column_name
                    if backwards
                    else rename_column.new_db_column_name
                )

                await self._run_query(
                    _Table.alter().rename_column(
                        column=column,
                        new_name=new_name,
                    )
                )

    async def _run_add_tables(self, backwards: bool = False):
        table_classes: list[type[Table]] = []
        for add_table in self.add_tables:
            add_columns: list[AddColumnClass] = (
                self.add_columns.for_table_class_name(add_table.class_name)
            )
            _Table: type[Table] = create_table_class(
                class_name=add_table.class_name,
                class_kwargs={
                    "tablename": add_table.tablename,
                    "schema": add_table.schema,
                },
                class_members={
                    add_column.column._meta.name: add_column.column
                    for add_column in add_columns
                },
            )
            table_classes.append(_Table)

        # Sort by foreign key, so they're created in the right order.
        sorted_table_classes = sort_table_classes(table_classes)

        if backwards:
            for _Table in reversed(sorted_table_classes):
                await self._run_query(_Table.alter().drop_table(cascade=True))
        else:
            for _Table in sorted_table_classes:
                await self._run_query(_Table.create_table())

    async def _run_add_columns(self, backwards: bool = False):
        """
        Add columns, which belong to existing tables
        """
        if backwards:
            for add_column in self.add_columns.add_columns:
                if add_column.table_class_name in [
                    i.class_name for i in self.add_tables
                ]:
                    # Don't reverse the add column as the table is going to
                    # be deleted.
                    continue

                _Table = create_table_class(
                    class_name=add_column.table_class_name,
                    class_kwargs={
                        "tablename": add_column.tablename,
                        "schema": add_column.schema,
                    },
                )

                await self._run_query(
                    _Table.alter().drop_column(add_column.column)
                )
        else:
            for table_class_name in self.add_columns.table_class_names:
                if table_class_name in [i.class_name for i in self.add_tables]:
                    continue  # No need to add columns to new tables

                add_columns: list[AddColumnClass] = (
                    self.add_columns.for_table_class_name(table_class_name)
                )

                ###############################################################
                # Define the table, with the columns, so the metaclass
                # sets up the columns correctly.

                table_class_members = {
                    add_column.column._meta.name: add_column.column
                    for add_column in add_columns
                }

                # There's an extreme edge case, when we're adding a foreign
                # key which references its own table, for example:
                #
                #   fk = ForeignKey('self')
                #
                # And that table has a custom primary key, for example:
                #
                #   id = UUID(primary_key=True)
                #
                # In this situation, we need to know the primary key of the
                # table in order to correctly add this new foreign key.
                for add_column in add_columns:
                    if (
                        isinstance(add_column.column, ForeignKey)
                        and add_column.column._meta.params.get("references")
                        == "self"
                    ):
                        try:
                            existing_table = (
                                await self.get_table_from_snapshot(
                                    table_class_name=table_class_name,
                                    app_name=self.app_name,
                                    offset=-1,
                                )
                            )
                        except ValueError:
                            logger.error(
                                "Unable to find primary key for the table - "
                                "assuming Serial."
                            )
                        else:
                            primary_key = existing_table._meta.primary_key

                            table_class_members[primary_key._meta.name] = (
                                primary_key
                            )

                        break

                _Table = create_table_class(
                    class_name=add_columns[0].table_class_name,
                    class_kwargs={
                        "tablename": add_columns[0].tablename,
                        "schema": add_columns[0].schema,
                    },
                    class_members=table_class_members,
                )

                ###############################################################

                for add_column in add_columns:
                    # We fetch the column from the Table, as the metaclass
                    # copies and sets it up properly.
                    column = _Table._meta.get_column_by_name(
                        add_column.column._meta.name
                    )

                    await self._run_query(
                        _Table.alter().add_column(
                            name=column._meta.name, column=column
                        )
                    )
                    if add_column.column._meta.index:
                        await self._run_query(
                            _Table.create_index([add_column.column])
                        )

    async def _run_change_table_schema(self, backwards: bool = False):
        from piccolo.schema import SchemaManager

        schema_manager = SchemaManager()

        for change_table_schema in self.change_table_schemas:
            if backwards:
                # Note, we don't try dropping any schemas we may have created.
                # It's dangerous to do so, just in case the user manually
                # added tables etc to the schema, and we delete them.

                if (
                    change_table_schema.old_schema
                    and change_table_schema.old_schema != "public"
                ):
                    await self._run_query(
                        schema_manager.create_schema(
                            schema_name=change_table_schema.old_schema,
                            if_not_exists=True,
                        )
                    )

                await self._run_query(
                    schema_manager.move_table(
                        table_name=change_table_schema.tablename,
                        new_schema=change_table_schema.old_schema or "public",
                        current_schema=change_table_schema.new_schema,
                    )
                )

            else:
                if (
                    change_table_schema.new_schema
                    and change_table_schema.new_schema != "public"
                ):
                    await self._run_query(
                        schema_manager.create_schema(
                            schema_name=change_table_schema.new_schema,
                            if_not_exists=True,
                        )
                    )

                await self._run_query(
                    schema_manager.move_table(
                        table_name=change_table_schema.tablename,
                        new_schema=change_table_schema.new_schema or "public",
                        current_schema=change_table_schema.old_schema,
                    )
                )

    async def run(self, backwards: bool = False):
        direction = "backwards" if backwards else "forwards"
        if self.preview:
            direction = "preview " + direction
        print(f"  - {self.migration_id} [{direction}]... ", end="")

        engine = engine_finder()

        if not engine:
            raise Exception("Can't find engine")

        async with (
            engine.transaction()
            if self.wrap_in_transaction
            else SkippedTransaction()
        ):
            if not self.preview:
                if direction == "backwards":
                    raw_list = self.raw_backwards
                else:
                    raw_list = self.raw

                for raw in raw_list:
                    if inspect.iscoroutinefunction(raw):
                        await raw()
                    else:
                        raw()

            await self._run_add_tables(backwards=backwards)
            await self._run_change_table_schema(backwards=backwards)
            await self._run_rename_tables(backwards=backwards)
            await self._run_add_columns(backwards=backwards)
            await self._run_drop_columns(backwards=backwards)
            await self._run_drop_tables(backwards=backwards)
            await self._run_rename_columns(backwards=backwards)
            # We can remove this for cockroach when resolved.
            # https://github.com/cockroachdb/cockroach/issues/49351
            # "ALTER COLUMN TYPE is not supported inside a transaction"
            if engine.engine_type != "cockroach":
                await self._run_alter_columns(backwards=backwards)

        if engine.engine_type == "cockroach":
            await self._run_alter_columns(backwards=backwards)
