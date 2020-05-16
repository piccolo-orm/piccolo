from dataclasses import dataclass
import typing as t


@dataclass
class RenameTable:
    old_class_name: str
    old_tablename: str
    new_class_name: str
    new_tablename: str


@dataclass
class RenameColumn:
    table_class_name: str
    tablename: str
    old_column_name: str
    new_column_name: str


@dataclass
class AlterColumn:
    table_class_name: str
    column_name: str
    tablename: str
    params: t.Dict[str, t.Any]
    old_params: t.Dict[str, t.Any]


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
