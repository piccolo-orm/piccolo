from piccolo.table import Table
from piccolo.columns import Varchar, Boolean


class Task(Table):
    """
    An example table.
    """

    name = Varchar()
    completed = Boolean(default=False)
