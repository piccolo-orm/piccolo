from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
import datetime
from enum import Enum
from inspect import isclass
import typing as t

from piccolo.columns.base import Column
from piccolo.apps.migrations.auto.operations import (
    AddColumn,
    DropColumn,
    AlterColumn,
)
from piccolo.table import Table


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
        print(
            "Default arguments which are functions are not currently supported"
        )
        params["default"] = None

    for key, value in params.items():
        # Convert enums into plain values
        if isinstance(value, Enum):
            params[key] = f"{value.__class__.__name__}.{value.name}"

        # Replace any Table class values into class names
        if isclass(value) and issubclass(value, Table):
            params[key] = f"{value.__name__}|{value._meta.tablename}"

        # Convert any datetime values into isoformat strings
        if isinstance(value, datetime.datetime):
            params[key] = value.isoformat()

    return params


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
            existing_column = self.columns_map.get(column._meta.name)
            if not existing_column:
                # This is a new column - already captured above.
                continue
            delta = compare_dicts(
                serialise_params(column._meta.params),
                serialise_params(existing_column._meta.params),
            )
            old_params = serialise_params(
                {
                    key: existing_column._meta.params.get(key)
                    for key, _ in delta.items()
                }
            )

            if delta:
                alter_columns.append(
                    AlterColumn(
                        table_class_name=self.class_name,
                        tablename=self.tablename,
                        column_name=column._meta.name,
                        params=delta,
                        old_params=old_params,
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
        _Table: t.Type[Table] = type(
            self.class_name,
            (Table,),
            {column._meta.name: column for column in self.columns},
        )
        _Table._meta.tablename = self.tablename
        return _Table
