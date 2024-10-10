# tables.py

from piccolo.columns import ForeignKey, Varchar
from piccolo.table import Table
from piccolo.utils.pydantic import create_pydantic_model


class Band(Table):
    name = Varchar()
    # This automatically gets converted into a LazyTableReference, because a
    # string is passed in:
    manager = ForeignKey("Manager")


# This is not recommended, as it will cause the LazyTableReference to be
# evaluated before Manager has imported.
# Instead, move this to a separate file, or below Manager.
BandModel = create_pydantic_model(Band)


class Manager(Table):
    name = Varchar()
