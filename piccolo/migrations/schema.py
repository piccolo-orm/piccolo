"""
Used to generate and modify database tables.

How can I make tables easily diffable???

Work from a theoretical picture of how the database should look, or work from
the actual db???

Work from theoretical ...

AddColumn / DropColumn / ModifyColumn all need to be combinable.

Also, the attributes also need to be combinable.

Rather than them being directly combinable, they just manipulate a schema
object. Add and delete operations are processed first.

Just make the Schema's combinable.

"""
from __future__ import annotations
# TODO - not used much yet. Remove???

# Consists of a bunch of operators
# create_column
# create_table
# modify_column (rename, null / not null, max_chars, change type)
# drop_column
# We already have alter ...


class Schema():

    def __init__(self, column_changes, table_changes):
        self.column_changes = column_changes
        self.table_changes = table_changes

    def __add__(self, value: Schema) -> Schema:
        """
        We add schema objects together to get a picture of the schema at
        a point in time.
        """
        self.column_changes += value.column_changes
        self.table_changes += value.table_changes
        return self


class CreateTable():
    def __init__(self):
        pass


class ModifyTable():
    """
    Does things like renaming the table.
    """
    def __init__(self):
        pass


class CreateColumn():
    def __init__(self):
        pass


class ModifyColumn():
    def __init__(self):
        pass


class DropColumn():
    def __init__(self, table_name: str, column_name: str) -> None:
        self.table_name = table_name
        self.column_name = column_name

    def __str__(self):
        return f'DROP COLUMN {self.column_name} from {self.table_name};'
