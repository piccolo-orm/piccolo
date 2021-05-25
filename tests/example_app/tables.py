from enum import Enum

from piccolo.table import Table
from piccolo.columns import Varchar, ForeignKey, Integer, Numeric, Text
from piccolo.columns.choices import Choice


###############################################################################
# Simple example


class Manager(Table):
    name = Varchar(length=50)


class Band(Table):
    name = Varchar(length=50)
    manager = ForeignKey(Manager, null=True)
    popularity = Integer(default=0)


###############################################################################
# More complex


class Venue(Table):
    name = Varchar(length=100)
    capacity = Integer(default=0)


class Concert(Table):
    band_1 = ForeignKey(Band)
    band_2 = ForeignKey(Band)
    venue = ForeignKey(Venue)


class Ticket(Table):
    price = Numeric(digits=(5, 2))


class Poster(Table, tags=["special"]):
    """
    Has tags for tests which need it.
    """

    content = Text()


class Shirt(Table):
    """
    Used for testing columns with a choices attribute.
    """

    class Size(str, Enum):
        small = "s"
        medium = "m"
        large = "l"

    size = Varchar(length=1, choices=Size, default=Size.large)
