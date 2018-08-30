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

"""

# Consists of a bunch of operators
# create_column
# create_table
# modify_column (rename, null / not null, max_chars, change type)
# drop_column


class CreateTable():
    def __init__(self):
        pass


class CreateColumn():
    def __init__(self):
        pass


class ModifyColumn():
    def __init__(self):
        pass


class DropColumn():
    def __init__(self, table_name: str, column_name: str):
        self.table_name = table_name
        self.column_name = column_name

    def __str__(self):
        return f'DROP COLUMN {self.column_name} from {self.table_name};'
