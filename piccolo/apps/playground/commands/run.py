"""
Populates a database with an example schema and data, and launches a shell
for interacting with the data using Piccolo.
"""
import sys

from piccolo import table
from piccolo import columns
from piccolo.engine.base import Engine
from piccolo.engine import SQLiteEngine, PostgresEngine


class Manager(table.Table):
    name = columns.Varchar(length=50)


class Band(table.Table):
    name = columns.Varchar(length=50)
    manager = columns.ForeignKey(references=Manager, null=True)
    popularity = columns.Integer()


class Venue(table.Table):
    name = columns.Varchar(length=100)
    capacity = columns.Integer(default=0)


class Concert(table.Table):
    band_1 = columns.ForeignKey(Band)
    band_2 = columns.ForeignKey(Band)
    venue = columns.ForeignKey(Venue)


TABLES = (Manager, Band, Venue, Concert)


def populate():
    """
    Drop then recreate the tables, and populate with data.
    """
    for _table in reversed(TABLES):
        try:
            if _table.table_exists().run_sync():
                _table.alter().drop_table().run_sync()
        except Exception as e:
            print(e)

    for _table in TABLES:
        try:
            _table.create_table().run_sync()
        except Exception as e:
            print(e)

    guido = Manager(name="Guido")
    guido.save().run_sync()

    pythonistas = Band(name="Pythonistas", manager=guido.id, popularity=1000)
    pythonistas.save().run_sync()

    graydon = Manager(name="Graydon")
    graydon.save().run_sync()

    rustaceans = Band(name="Rustaceans", manager=graydon.id, popularity=500)
    rustaceans.save().run_sync()

    venue = Venue(name="Amazing Venue", capacity=5000)
    venue.save().run_sync()

    concert = Concert(
        band_1=pythonistas.id, band_2=rustaceans.id, venue=venue.id
    )
    concert.save().run_sync()


def run(
    engine: str = "sqlite",
    user: str = "piccolo",
    password: str = "piccolo",
    database: str = "piccolo_playground",
    host: str = "localhost",
    port: int = 5432,
):
    """
    Creates a test database to play with.

    :param engine:
        Which database engine to use - options are sqlite or postgres
    :param user:
        Postgres user
    :param password:
        Postgres password
    :param database:
        Postgres database
    :param host:
        Postgres host
    :param port:
        Postgres port
    """
    try:
        import IPython
    except ImportError:
        print(
            "Install iPython using `pip install ipython==7.6.1` to use this "
            "feature."
        )
        sys.exit(1)

    if engine.upper() == "POSTGRES":
        db: Engine = PostgresEngine(
            {
                "host": host,
                "database": database,
                "user": user,
                "password": password,
                "port": port,
            }
        )
        for _table in TABLES:
            _table._meta._db = db
    else:
        db = SQLiteEngine()
        for _table in TABLES:
            _table._meta._db = db

    print("Tables:\n")

    for _table in TABLES:
        print(_table._table_str(abbreviated=True))
        print("\n")

    populate()
    IPython.embed()
