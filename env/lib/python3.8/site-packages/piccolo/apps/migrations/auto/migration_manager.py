from __future__ import annotations

import inspect
import typing as t
from dataclasses import dataclass, field

from piccolo.apps.migrations.auto.diffable_table import DiffableTable
from piccolo.apps.migrations.auto.operations import (
    AlterColumn,
    DropColumn,
    RenameColumn,
    RenameTable,
)
from piccolo.apps.migrations.auto.serialisation import deserialise_params
from piccolo.columns import Column, column_types
from piccolo.columns.column_types import Serial
from piccolo.engine import engine_finder
from piccolo.query import Query
from piccolo.query.base import DDL
from piccolo.table import Table, create_table_class, sort_table_classes
from piccolo.utils.warnings import colored_warning


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
        return list({i.table_class_name for i in self.add_columns})


@dataclass
class DropColumnCollection:
    drop_columns: t.List[DropColumn] = field(default_factory=list)

    def append(self, drop_column: DropColumn):
        self.drop_columns.append(drop_column)

    def for_table_class_name(
        self, table_class_name: str
    ) -> t.List[DropColumn]:
        return [
            i
            for i in self.drop_columns
            if i.table_class_name == table_class_name
        ]

    @property
    def table_class_names(self) -> t.List[str]:
        return list({i.table_class_name for i in self.drop_columns})


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
        return list({i.table_class_name for i in self.rename_columns})


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
        return list({i.table_class_name for i in self.alter_columns})


@dataclass
class MigrationManager:
    """
    Each auto generated migration returns a MigrationManager. It contains
    all of the schema changes that migration wants to make.
    """

    migration_id: str = ""
    app_name: str = ""
    description: str = ""
    preview: bool = False
    add_tables: t.List[DiffableTable] = field(default_factory=list)
    drop_tables: t.List[DiffableTable] = field(default_factory=list)
    rename_tables: t.List[RenameTable] = field(default_factory=list)
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
    raw: t.List[t.Union[t.Callable, t.Coroutine]] = field(default_factory=list)
    raw_backwards: t.List[t.Union[t.Callable, t.Coroutine]] = field(
        default_factory=list
    )

    def add_table(
        self,
        class_name: str,
        tablename: str,
        columns: t.Optional[t.List[Column]] = None,
    ):
        if not columns:
            columns = []

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
        self,
        old_class_name: str,
        old_tablename: str,
        new_class_name: str,
        new_tablename: str,
    ):
        self.rename_tables.append(
            RenameTable(
                old_class_name=old_class_name,
                old_tablename=old_tablename,
                new_class_name=new_class_name,
                new_tablename=new_tablename,
            )
        )

    def add_column(
        self,
        table_class_name: str,
        tablename: str,
        column_name: str,
        db_column_name: t.Optional[str] = None,
        column_class_name: str = "",
        column_class: t.Optional[t.Type[Column]] = None,
        params: t.Dict[str, t.Any] = None,
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
        column._meta.db_column_name = db_column_name

        self.add_columns.append(
            AddColumnClass(
                column=column,
                tablename=tablename,
                table_class_name=table_class_name,
            )
        )

    def drop_column(
        self,
        table_class_name: str,
        tablename: str,
        column_name: str,
        db_column_name: t.Optional[str] = None,
    ):
        self.drop_columns.append(
            DropColumn(
                table_class_name=table_class_name,
                column_name=column_name,
                db_column_name=db_column_name or column_name,
                tablename=tablename,
            )
        )

    def rename_column(
        self,
        table_class_name: str,
        tablename: str,
        old_column_name: str,
        new_column_name: str,
        old_db_column_name: t.Optional[str] = None,
        new_db_column_name: t.Optional[str] = None,
    ):
        self.rename_columns.append(
            RenameColumn(
                table_class_name=table_class_name,
                tablename=tablename,
                old_column_name=old_column_name,
                new_column_name=new_column_name,
                old_db_column_name=old_db_column_name or old_column_name,
                new_db_column_name=new_db_column_name or new_column_name,
            )
        )

    def alter_column(
        self,
        table_class_name: str,
        tablename: str,
        column_name: str,
        db_column_name: t.Optional[str] = None,
        params: t.Dict[str, t.Any] = None,
        old_params: t.Dict[str, t.Any] = None,
        column_class: t.Optional[t.Type[Column]] = None,
        old_column_class: t.Optional[t.Type[Column]] = None,
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
            )
        )

    def add_raw(self, raw: t.Union[t.Callable, t.Coroutine]):
        """
        A migration manager can execute arbitrary functions or coroutines when
        run. This is useful if you want to execute raw SQL.
        """
        self.raw.append(raw)

    def add_raw_backwards(self, raw: t.Union[t.Callable, t.Coroutine]):
        """
        When reversing a migration, you may want to run extra code to help
        clean up.
        """
        self.raw_backwards.append(raw)

    ###########################################################################

    async def get_table_from_snapshot(
        self,
        table_class_name: str,
        app_name: t.Optional[str],
        offset: int = 0,
        migration_id: t.Optional[str] = None,
    ) -> t.Type[Table]:
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
    async def _print_query(query: t.Union[DDL, Query]):
        if isinstance(query, DDL):
            print("\n", ";".join(query.ddl) + ";")
        else:
            print(str(query))

    async def _run_query(self, query: t.Union[DDL, Query]):
        """
        If MigrationManager is not in the preview mode,
         executes the queries. else, prints the query.
        """
        if self.preview:
            await self._print_query(query)
        else:
            await query.run()

    async def _run_alter_columns(self, backwards=False):
        for table_class_name in self.alter_columns.table_class_names:
            alter_columns = self.alter_columns.for_table_class_name(
                table_class_name
            )

            if not alter_columns:
                continue

            _Table: t.Type[Table] = create_table_class(
                class_name=table_class_name,
                class_kwargs={"tablename": alter_columns[0].tablename},
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

                        using_expression: t.Optional[str] = None

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

    async def _run_drop_columns(self, backwards=False):
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

                _Table: t.Type[Table] = create_table_class(
                    class_name=table_class_name,
                    class_kwargs={"tablename": columns[0].tablename},
                )

                for column in columns:
                    await self._run_query(
                        _Table.alter().drop_column(column=column.column_name)
                    )

    async def _run_rename_tables(self, backwards=False):
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

            _Table: t.Type[Table] = create_table_class(
                class_name=class_name, class_kwargs={"tablename": tablename}
            )

            await self._run_query(
                _Table.alter().rename_table(new_name=new_tablename)
            )

    async def _run_rename_columns(self, backwards=False):
        for table_class_name in self.rename_columns.table_class_names:
            columns = self.rename_columns.for_table_class_name(
                table_class_name
            )

            if not columns:
                continue

            _Table: t.Type[Table] = create_table_class(
                class_name=table_class_name,
                class_kwargs={"tablename": columns[0].tablename},
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

    async def _run_add_tables(self, backwards=False):
        table_classes: t.List[t.Type[Table]] = []
        for add_table in self.add_tables:
            add_columns: t.List[
                AddColumnClass
            ] = self.add_columns.for_table_class_name(add_table.class_name)
            _Table: t.Type[Table] = create_table_class(
                class_name=add_table.class_name,
                class_kwargs={"tablename": add_table.tablename},
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

    async def _run_add_columns(self, backwards=False):
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

                _Table: t.Type[Table] = create_table_class(
                    class_name=add_column.table_class_name,
                    class_kwargs={"tablename": add_column.tablename},
                )

                await self._run_query(
                    _Table.alter().drop_column(add_column.column)
                )
        else:
            for table_class_name in self.add_columns.table_class_names:
                if table_class_name in [i.class_name for i in self.add_tables]:
                    continue  # No need to add columns to new tables

                add_columns: t.List[
                    AddColumnClass
                ] = self.add_columns.for_table_class_name(table_class_name)

                # Define the table, with the columns, so the metaclass
                # sets up the columns correctly.
                _Table: t.Type[Table] = create_table_class(
                    class_name=add_columns[0].table_class_name,
                    class_kwargs={"tablename": add_columns[0].tablename},
                    class_members={
                        add_column.column._meta.name: add_column.column
                        for add_column in add_columns
                    },
                )

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

    async def run(self, backwards=False):
        direction = "backwards" if backwards else "forwards"
        if self.preview:
            direction = "preview " + direction
        print(f"  - {self.migration_id} [{direction}]... ", end="")

        engine = engine_finder()

        if not engine:
            raise Exception("Can't find engine")

        async with engine.transaction():

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
