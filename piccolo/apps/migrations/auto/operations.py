import typing as t
from dataclasses import dataclass

from piccolo.columns.base import Column


@dataclass
class RenameTable:
    old_class_name: str
    old_tablename: str
    new_class_name: str
    new_tablename: str
    schema: t.Optional[str] = None


@dataclass
class ChangeTableSchema:
    class_name: str
    tablename: str
    old_schema: t.Optional[str]
    new_schema: t.Optional[str]


@dataclass
class RenameColumn:
    table_class_name: str
    tablename: str
    old_column_name: str
    new_column_name: str
    old_db_column_name: str
    new_db_column_name: str
    schema: t.Optional[str] = None


@dataclass
class AlterColumn:
    table_class_name: str
    column_name: str
    db_column_name: str
    tablename: str
    params: t.Dict[str, t.Any]
    old_params: t.Dict[str, t.Any]
    column_class: t.Optional[t.Type[Column]] = None
    old_column_class: t.Optional[t.Type[Column]] = None
    schema: t.Optional[str] = None


@dataclass
class DropColumn:
    table_class_name: str
    column_name: str
    db_column_name: str
    tablename: str
    schema: t.Optional[str] = None


@dataclass
class AddColumn:
    table_class_name: str
    column_name: str
    db_column_name: str
    column_class_name: str
    column_class: t.Type[Column]
    params: t.Dict[str, t.Any]
    schema: t.Optional[str] = None
