from enum import Enum

from piccolo.columns import (
    JSON,
    JSONB,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    Varchar,
)
from piccolo.columns.readable import Readable
from piccolo.table import Table

###############################################################################
# Simple example


class Manager(Table):
    name = Varchar(length=50)

    @classmethod
    def get_readable(cls) -> Readable:
        return Readable(template="%s", columns=[cls.name])


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
    concert = ForeignKey(Concert)
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


class RecordingStudio(Table):
    """
    Used for testing JSON and JSONB columns.
    """

    facilities = JSON()
    facilities_b = JSONB()
