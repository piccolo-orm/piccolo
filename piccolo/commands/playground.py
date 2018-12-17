"""
Populates a database with an example schema and data, and launches a shell
for interacting with the data using Piccolo.
"""
import sys

import click

from piccolo import table
from piccolo import columns
from piccolo.engine import PostgresEngine


DB = PostgresEngine({
    'host': 'localhost',
    'database': 'piccolo_playground',
    'user': 'piccolo',
    'password': 'piccolo'
})


class Manager(table.Table):
    name = columns.Varchar(length=50)

    class Meta():
        db = DB


class Band(table.Table):
    name = columns.Varchar(length=50)
    manager = columns.ForeignKey(references=Manager)
    popularity = columns.Integer()

    class Meta():
        db = DB


class Venue(table.Table):
    name = columns.Varchar(length=100)
    capacity = columns.Integer()

    class Meta():
        db = DB


class Concert(table.Table):
    band_1 = columns.ForeignKey(Band)
    band_2 = columns.ForeignKey(Band)
    venue = columns.ForeignKey(Venue)

    class Meta():
        db = DB



def populate():
    """
    Drop then recreate the tables, and populate with data.
    """
    tables = (Manager, Band, Venue, Concert)
    for table in tables:
        try:
            table.drop.run_sync()
        except Exception as e:
            print(e)

    for table in tables:
        try:
            table.create.run_sync()
        except Exception as e:
            print(e)

    guido = Manager(name="Guido")
    guido.save().run_sync()

    pythonistas = Band(
        name="Pythonistas",
        manager=guido.id,
        popularity=1000
    )
    pythonistas.save().run_sync()

    graydon = Manager(name="Graydon")
    graydon.save().run_sync()

    rustaceans = Band(
        name="Rustaceans",
        manager=graydon.id,
        popularity=500
    )
    rustaceans.save().run_sync()

    venue = Venue(
        name="Amazing Venue",
        capacity=5000
    )
    venue.save().run_sync()

    concert = Concert(
        band_1=pythonistas.id,
        band_2=rustaceans.id,
        venue=venue.id
    )
    concert.save().run_sync()


@click.command(name="playground")
def playground():
    """
    Creates a test database to play with.
    """
    try:
        import IPython
    except ImportError:
        print(
            "Install iPython using `pip install ipython` to use this feature."
        )
        sys.exit(1)

    populate()
    IPython.embed()
