from dataclasses import dataclass
from typing import Any, Optional

from piccolo.columns.base import Column


@dataclass
class RenameTable:
    old_class_name: str
    old_tablename: str
    new_class_name: str
    new_tablename: str
    schema: Optional[str] = None


@dataclass
class ChangeTableSchema:
    class_name: str
    tablename: str
    old_schema: Optional[str]
    new_schema: Optional[str]


@dataclass
class RenameColumn:
    table_class_name: str
    tablename: str
    old_column_name: str
    new_column_name: str
    old_db_column_name: str
    new_db_column_name: str
    schema: Optional[str] = None


@dataclass
class AlterColumn:
    table_class_name: str
    column_name: str
    db_column_name: str
    tablename: str
    params: dict[str, Any]
    old_params: dict[str, Any]
    column_class: Optional[type[Column]] = None
    old_column_class: Optional[type[Column]] = None
    schema: Optional[str] = None


@dataclass
class DropColumn:
    table_class_name: str
    column_name: str
    db_column_name: str
    tablename: str
    schema: Optional[str] = None


@dataclass
class AddColumn:
    table_class_name: str
    column_name: str
    db_column_name: str
    column_class_name: str
    column_class: type[Column]
    params: dict[str, Any]
    schema: Optional[str] = None
