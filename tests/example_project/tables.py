from aragorm import table
from aragorm import columns
from aragorm.engine import PostgresEngine


DB = PostgresEngine({
    'host': 'localhost',
    'database': 'aragorm',
    'user': 'aragorm',
    'password': 'aragorm'
})


###############################################################################
# Simple example

class Pokemon(table.Table):
    name = columns.Varchar(length=50)
    trainer = columns.Varchar(length=20)
    power = columns.Integer()

    class Meta():
        db = DB


class Trainer(table.Table):
    name = columns.Varchar(length=50)

    class Meta():
        db = DB


###############################################################################
# More complex

class Stadium(table.Table):
    name = columns.Varchar(length=100)
    capacity = columns.Integer()

    class Meta():
        db = DB


class Match(table.Table):
    pokemon_1 = columns.ForeignKey(Pokemon)
    pokemon_2 = columns.ForeignKey(Pokemon)
    stadium = columns.ForeignKey(Stadium)

    class Meta():
        db = DB
