from __future__ import annotations

import inspect
import typing as t
from dataclasses import dataclass

from piccolo.columns.base import Selectable
from piccolo.columns.column_types import (
    JSON,
    JSONB,
    Column,
    ForeignKey,
    LazyTableReference,
)
from piccolo.utils.sync import run_sync

if t.TYPE_CHECKING:
    from piccolo.table import Table


class M2MSelect(Selectable):
    """
    This is a subquery used within a select to fetch data via an M2M table.
    """

    def __init__(
        self,
        *columns: Column,
        m2m: M2M,
        as_list: bool = False,
        load_json: bool = False,
    ):
        """
        :param columns:
            Which columns to include from the related table.
        :param as_list:
            If a single column is provided, and ``as_list`` is ``True`` a
            flattened list will be returned, rather than a list of objects.
        :param load_json:
            If ``True``, any JSON strings are loaded as Python objects.

        """
        self.as_list = as_list
        self.columns = columns
        self.m2m = m2m
        self.load_json = load_json

        safe_types = [int, str]

        # If the columns can be serialised / deserialise as JSON, then we
        # can fetch the data all in one go.
        self.serialisation_safe = all(
            (column.__class__.value_type in safe_types)
            and (type(column) not in (JSON, JSONB))
            for column in columns
        )

    def get_select_string(self, engine_type: str, just_alias=False) -> str:
        m2m_table_name = self.m2m._meta.resolved_joining_table._meta.tablename
        m2m_relationship_name = self.m2m._meta.name

        fk_1 = self.m2m._meta.primary_foreign_key
        fk_1_name = fk_1._meta.db_column_name
        table_1 = fk_1._foreign_key_meta.resolved_references
        table_1_name = table_1._meta.tablename
        table_1_pk_name = table_1._meta.primary_key._meta.db_column_name

        fk_2 = self.m2m._meta.secondary_foreign_key
        fk_2_name = fk_2._meta.db_column_name
        table_2 = fk_2._foreign_key_meta.resolved_references
        table_2_name = table_2._meta.tablename
        table_2_pk_name = table_2._meta.primary_key._meta.db_column_name

        inner_select = f"""
            "{m2m_table_name}"
            JOIN "{table_1_name}" "inner_{table_1_name}" ON (
                "{m2m_table_name}"."{fk_1_name}" = "inner_{table_1_name}"."{table_1_pk_name}"
            )
            JOIN "{table_2_name}" "inner_{table_2_name}" ON (
                "{m2m_table_name}"."{fk_2_name}" = "inner_{table_2_name}"."{table_2_pk_name}"
            )
            WHERE "{m2m_table_name}"."{fk_1_name}" = "{table_1_name}"."{table_1_pk_name}"
        """  # noqa: E501

        if engine_type == "postgres":
            if self.as_list:
                column_name = self.columns[0]._meta.db_column_name
                return f"""
                    ARRAY(
                        SELECT
                            "inner_{table_2_name}"."{column_name}"
                        FROM {inner_select}
                    ) AS "{m2m_relationship_name}"
                """
            elif not self.serialisation_safe:
                column_name = table_2_pk_name
                return f"""
                    ARRAY(
                        SELECT
                            "inner_{table_2_name}"."{column_name}"
                        FROM {inner_select}
                    ) AS "{m2m_relationship_name}"
                """
            else:
                column_names = ", ".join(
                    f'"inner_{table_2_name}"."{column._meta.db_column_name}"'
                    for column in self.columns
                )
                return f"""
                    (
                        SELECT JSON_AGG({m2m_relationship_name}_results)
                        FROM (
                            SELECT {column_names} FROM {inner_select}
                        ) AS "{m2m_relationship_name}_results"
                    ) AS "{m2m_relationship_name}"
                """
        elif engine_type == "sqlite":
            if len(self.columns) > 1 or not self.serialisation_safe:
                column_name = table_2_pk_name
            else:
                column_name = self.columns[0]._meta.db_column_name

            return f"""
                (
                    SELECT group_concat(
                        "inner_{table_2_name}"."{column_name}"
                    )
                    FROM {inner_select}
                )
                AS "{m2m_relationship_name} [M2M]"
            """
        else:
            raise ValueError(f"{engine_type} is an unrecognised engine type")


@dataclass
class M2MMeta:
    joining_table: t.Union[t.Type[Table], LazyTableReference]
    _foreign_key_columns: t.Optional[t.List[ForeignKey]] = None

    # Set by the Table Metaclass:
    _name: t.Optional[str] = None
    _table: t.Optional[t.Type[Table]] = None

    @property
    def name(self) -> str:
        if not self._name:
            raise ValueError(
                "`_name` isn't defined - the Table Metaclass should set it."
            )
        return self._name

    @property
    def table(self) -> t.Type[Table]:
        if not self._table:
            raise ValueError(
                "`_table` isn't defined - the Table Metaclass should set it."
            )
        return self._table

    @property
    def resolved_joining_table(self) -> t.Type[Table]:
        """
        Evaluates the ``joining_table`` attribute if it's a
        ``LazyTableReference``, raising a ``ValueError`` if it fails, otherwise
        returns a ``Table`` subclass.
        """
        from piccolo.table import Table

        if isinstance(self.joining_table, LazyTableReference):
            return self.joining_table.resolve()
        elif inspect.isclass(self.joining_table) and issubclass(
            self.joining_table, Table
        ):
            return self.joining_table
        else:
            raise ValueError(
                "The joining_table attribute is neither a Table subclass or a "
                "LazyTableReference instance."
            )

    @property
    def foreign_key_columns(self) -> t.List[ForeignKey]:
        if not self._foreign_key_columns:
            self._foreign_key_columns = (
                self.resolved_joining_table._meta.foreign_key_columns[:2]
            )
        return self._foreign_key_columns

    @property
    def primary_foreign_key(self) -> ForeignKey:
        """
        The joining table has two foreign keys. We need a way to distinguish
        between them. The primary is the one which points to the table with
        ``M2M`` defined on it. In this example the primary foreign key is the
        one which points to ``Band``:

        .. code-block:: python

            class Band(Table):
                name = Varchar()
                genres = M2M(
                    LazyTableReference("GenreToBand", module_path=__name__)
                )

            class Genre(Table):
                name = Varchar()

            class GenreToBand(Table):
                band = ForeignKey(Band)  # primary
                genre = ForeignKey(Genre)  # secondary

        The secondary foreign key is the one which points to ``Genre``.

        """
        for fk_column in self.foreign_key_columns:
            if fk_column._foreign_key_meta.resolved_references == self.table:
                return fk_column

        raise ValueError("No matching foreign key column found!")

    @property
    def primary_table(self) -> t.Type[Table]:
        return self.primary_foreign_key._foreign_key_meta.resolved_references

    @property
    def secondary_foreign_key(self) -> ForeignKey:
        """
        See ``primary_foreign_key``.
        """
        for fk_column in self.foreign_key_columns:
            if fk_column._foreign_key_meta.resolved_references != self.table:
                return fk_column

        raise ValueError("No matching foreign key column found!")

    @property
    def secondary_table(self) -> t.Type[Table]:
        return self.secondary_foreign_key._foreign_key_meta.resolved_references


@dataclass
class M2MAddRelated:

    target_row: Table
    m2m: M2M
    rows: t.Sequence[Table]
    extra_column_values: t.Dict[t.Union[Column, str], t.Any]

    def __post_init__(self):
        # Normalise `extra_column_values`, so we just have the column names.
        self.extra_column_values: t.Dict[str, t.Any] = {
            i._meta.name if isinstance(i, Column) else i: j
            for i, j in self.extra_column_values.items()
        }

    async def run(self):
        rows = self.rows
        unsaved = [i for i in rows if not i._exists_in_db]

        async with rows[0]._meta.db.transaction():
            if unsaved:
                await rows[0].__class__.insert(*unsaved).run()

            joining_table = self.m2m._meta.resolved_joining_table

            joining_table_rows = []

            for row in rows:
                joining_table_row = joining_table(**self.extra_column_values)
                setattr(
                    joining_table_row,
                    self.m2m._meta.primary_foreign_key._meta.name,
                    getattr(
                        self.target_row,
                        self.target_row._meta.primary_key._meta.name,
                    ),
                )
                setattr(
                    joining_table_row,
                    self.m2m._meta.secondary_foreign_key._meta.name,
                    getattr(
                        row,
                        row._meta.primary_key._meta.name,
                    ),
                )
                joining_table_rows.append(joining_table_row)

            return await joining_table.insert(*joining_table_rows).run()

    def run_sync(self):
        return run_sync(self.run())

    def __await__(self):
        return self.run().__await__()


@dataclass
class M2MRemoveRelated:

    target_row: Table
    m2m: M2M
    rows: t.Sequence[Table]

    async def run(self):
        fk = self.m2m._meta.secondary_foreign_key
        related_table = fk._foreign_key_meta.resolved_references

        row_ids = []

        for row in self.rows:
            if row.__class__ != related_table:
                raise ValueError("The row belongs to the wrong table!")

            row_id = getattr(row, row._meta.primary_key._meta.name)
            if row_id:
                row_ids.append(row_id)

        if row_ids:
            return (
                await self.m2m._meta.resolved_joining_table.delete()
                .where(
                    self.m2m._meta.primary_foreign_key == self.target_row,
                    self.m2m._meta.secondary_foreign_key.is_in(row_ids),
                )
                .run()
            )

        return None

    def run_sync(self):
        return run_sync(self.run())

    def __await__(self):
        return self.run().__await__()


@dataclass
class M2MGetRelated:

    row: Table
    m2m: M2M

    async def run(self):
        joining_table = self.m2m._meta.resolved_joining_table

        secondary_table = self.m2m._meta.secondary_table

        # TODO - replace this with a subquery in the future.
        ids = (
            await joining_table.select(
                getattr(
                    self.m2m._meta.secondary_foreign_key,
                    secondary_table._meta.primary_key._meta.name,
                )
            )
            .where(self.m2m._meta.primary_foreign_key == self.row)
            .output(as_list=True)
        )

        results = await secondary_table.objects().where(
            secondary_table._meta.primary_key.is_in(ids)
        )

        return results

    def run_sync(self):
        return run_sync(self.run())

    def __await__(self):
        return self.run().__await__()


class M2M:
    def __init__(
        self,
        joining_table: t.Union[t.Type[Table], LazyTableReference],
        foreign_key_columns: t.Optional[t.List[ForeignKey]] = None,
    ):
        """
        :param joining_table:
            A ``Table`` containing two ``ForeignKey`` columns.
        :param foreign_key_columns:
            If for some reason your joining table has more than two foreign key
            columns, you can explicitly specify which two are relevant.

        """
        if foreign_key_columns and (
            len(foreign_key_columns) != 2
            or not all(isinstance(i, ForeignKey) for i in foreign_key_columns)
        ):
            raise ValueError("You must specify two ForeignKey columns.")

        self._meta = M2MMeta(
            joining_table=joining_table,
            _foreign_key_columns=foreign_key_columns,
        )

    def __call__(
        self, *columns: Column, as_list: bool = False, load_json: bool = False
    ) -> M2MSelect:
        """
        :param columns:
            Which columns to include from the related table. If none are
            specified, then all of the columns are returned.
        :param as_list:
            If a single column is provided, and ``as_list`` is ``True`` a
            flattened list will be returned, rather than a list of objects.
        :param load_json:
            If ``True``, any JSON strings are loaded as Python objects.
        """
        if len(columns) == 0:
            columns = tuple(self._meta.secondary_table._meta.columns)

        if as_list and len(columns) != 1:
            raise ValueError(
                "`as_list` is only valid with a single column argument"
            )

        return M2MSelect(
            *columns, m2m=self, as_list=as_list, load_json=load_json
        )
