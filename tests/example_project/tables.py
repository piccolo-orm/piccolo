from piccolo import table
from piccolo import columns


###############################################################################
# Simple example


class Manager(table.Table):
    name = columns.Varchar(length=50)


class Band(table.Table):
    name = columns.Varchar(length=50)
    manager = columns.ForeignKey(Manager)
    popularity = columns.Integer()


###############################################################################
# More complex


class Venue(table.Table):
    name = columns.Varchar(length=100)
    capacity = columns.Integer()


class Concert(table.Table):
    band_1 = columns.ForeignKey(Band)
    band_2 = columns.ForeignKey(Band)
    venue = columns.ForeignKey(Venue)
