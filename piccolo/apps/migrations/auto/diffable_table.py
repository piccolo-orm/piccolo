from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

from piccolo.apps.migrations.auto.operations import (
    AddColumn,
    AlterColumn,
    DropColumn,
)
from piccolo.apps.migrations.auto.serialisation import (
    deserialise_params,
    serialise_params,
)
from piccolo.columns.base import Column
from piccolo.table import Table, create_table_class


def compare_dicts(dict_1, dict_2) -> t.Dict[str, t.Any]:
    """
    Returns a new dictionary which only contains key, value pairs which are in
    the first dictionary and not the second.

    For example:
        dict_1 = {'a': 1, 'b': 2}
        dict_2 = {'a': 1}
        returns {'b': 2}

        dict_1 = {'a': 2, 'b': 2}
        dict_2 = {'a': 1}
        returns {'a': 2, 'b': 2}

    """
    output = {}

    for key, value in dict_1.items():

        dict_2_value = dict_2.get(key, ...)
        if dict_2_value is ...:
            output[key] = value
        else:
            if dict_2_value != value:
                output[key] = value

    return output


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


@dataclass
class ColumnComparison:
    """
    As Column overrides it's `__eq__` method, to allow it to be used in the
    `where` clause of a query, we need to wrap `Column` if we want to compare
    them.
    """

    column: Column

    def __hash__(self) -> int:
        return self.column.__hash__()

    def __eq__(self, value) -> bool:
        if isinstance(value, ColumnComparison):
            return self.column._meta.name == value.column._meta.name
        return False


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
                column_name=i.column._meta.name,
                column_class_name=i.column.__class__.__name__,
                column_class=i.column.__class__,
                params=i.column._meta.params,
            )
            for i in (
                {ColumnComparison(column=column) for column in self.columns}
                - {ColumnComparison(column=column) for column in value.columns}
            )
        ]

        drop_columns = [
            DropColumn(
                table_class_name=self.class_name,
                column_name=i.column._meta.name,
                tablename=value.tablename,
            )
            for i in (
                {ColumnComparison(column=column) for column in value.columns}
                - {ColumnComparison(column=column) for column in self.columns}
            )
        ]

        alter_columns: t.List[AlterColumn] = []

        for existing_column in value.columns:
            column = self.columns_map.get(existing_column._meta.name)
            if not column:
                # This is a new column - already captured above.
                continue

            delta = compare_dicts(
                serialise_params(column._meta.params).params,
                serialise_params(existing_column._meta.params).params,
            )

            old_params = {
                key: existing_column._meta.params.get(key)
                for key, _ in delta.items()
            }

            if delta or (column.__class__ != existing_column.__class__):
                alter_columns.append(
                    AlterColumn(
                        table_class_name=self.class_name,
                        tablename=self.tablename,
                        column_name=column._meta.name,
                        params=deserialise_params(delta),
                        old_params=old_params,
                        column_class=column.__class__,
                        old_column_class=existing_column.__class__,
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

    def to_table_class(self) -> t.Type[Table]:
        """
        Converts the DiffableTable into a Table subclass.
        """
        _Table: t.Type[Table] = create_table_class(
            class_name=self.class_name,
            class_kwargs={"tablename": self.tablename},
            class_members={
                column._meta.name: column for column in self.columns
            },
        )

        return _Table
