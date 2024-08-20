"""
Populates a database with an example schema and data, and launches a shell
for interacting with the data using Piccolo.
"""

import datetime
import sys
import uuid
from decimal import Decimal
from enum import Enum

from piccolo.columns import (
    JSON,
    UUID,
    Boolean,
    Date,
    ForeignKey,
    Integer,
    Interval,
    Numeric,
    Serial,
    Text,
    Timestamp,
    Varchar,
)
from piccolo.columns.readable import Readable
from piccolo.engine import PostgresEngine, SQLiteEngine
from piccolo.engine.base import Engine
from piccolo.table import Table
from piccolo.utils.warnings import colored_string


class Manager(Table):
    id: Serial
    name = Varchar(length=50)

    @classmethod
    def get_readable(cls) -> Readable:
        return Readable(
            template="%s",
            columns=[cls.name],
        )


class Band(Table):
    id: Serial
    name = Varchar(length=50)
    manager = ForeignKey(references=Manager, null=True)
    popularity = Integer()

    @classmethod
    def get_readable(cls) -> Readable:
        return Readable(
            template="%s",
            columns=[cls.name],
        )


class FanClub(Table):
    id: Serial
    address = Text()
    band = ForeignKey(Band, unique=True)


class Venue(Table):
    id: Serial
    name = Varchar(length=100)
    capacity = Integer(default=0)

    @classmethod
    def get_readable(cls) -> Readable:
        return Readable(
            template="%s",
            columns=[cls.name],
        )


class Concert(Table):
    id: Serial
    band_1 = ForeignKey(Band)
    band_2 = ForeignKey(Band)
    venue = ForeignKey(Venue)
    starts = Timestamp()
    duration = Interval()

    @classmethod
    def get_readable(cls) -> Readable:
        return Readable(
            template="%s and %s at %s",
            columns=[
                cls.band_1.name,
                cls.band_2.name,
                cls.venue.name,
            ],
        )


class Ticket(Table):
    class TicketType(Enum):
        sitting = "sitting"
        standing = "standing"
        premium = "premium"

    id: Serial
    concert = ForeignKey(Concert)
    price = Numeric(digits=(5, 2))
    ticket_type = Varchar(choices=TicketType, default=TicketType.standing)

    @classmethod
    def get_readable(cls) -> Readable:
        return Readable(
            template="%s - %s",
            columns=[
                cls.concert._.venue._.name,
                cls.ticket_type,
            ],
        )


class DiscountCode(Table):
    id: Serial
    code = UUID()
    active = Boolean(default=True, null=True)

    @classmethod
    def get_readable(cls) -> Readable:
        return Readable(
            template="%s - %s",
            columns=[cls.code, cls.active],
        )


class RecordingStudio(Table):
    id: Serial
    name = Varchar(length=100)
    facilities = JSON(null=True)

    @classmethod
    def get_readable(cls) -> Readable:
        return Readable(
            template="%s",
            columns=[cls.name],
        )


class Album(Table):
    id: Serial
    name = Varchar()
    band = ForeignKey(Band)
    release_date = Date()
    recorded_at = ForeignKey(RecordingStudio)

    @classmethod
    def get_readable(cls) -> Readable:
        return Readable(
            template="%s - %s",
            columns=[cls.name, cls.band._.name],
        )


TABLES = (
    Manager,
    Band,
    FanClub,
    Venue,
    Concert,
    Ticket,
    DiscountCode,
    RecordingStudio,
    Album,
)


def populate():
    """
    Drop then recreate the tables, and populate with data.
    """
    for _table in reversed(TABLES):
        try:
            _table.alter().drop_table(if_exists=True).run_sync()
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

    fan_club = FanClub(address="1 Flying Circus, UK", band=pythonistas)
    fan_club.save().run_sync()

    graydon = Manager(name="Graydon")
    graydon.save().run_sync()

    rustaceans = Band(name="Rustaceans", manager=graydon.id, popularity=500)
    rustaceans.save().run_sync()

    anders = Manager(name="Anders")
    anders.save().run_sync()

    c_sharps = Band(name="C-Sharps", popularity=700, manager=anders.id)
    c_sharps.save().run_sync()

    venue = Venue(name="Amazing Venue", capacity=5000)
    venue.save().run_sync()

    concert = Concert(
        band_1=pythonistas.id,
        band_2=rustaceans.id,
        venue=venue.id,
        starts=datetime.datetime.now() + datetime.timedelta(days=7),
        duration=datetime.timedelta(hours=2),
    )
    concert.save().run_sync()

    ticket = Ticket(concert=concert.id, price=Decimal("50.0"))
    ticket.save().run_sync()

    DiscountCode.insert(
        *[DiscountCode({DiscountCode.code: uuid.uuid4()}) for _ in range(5)]
    ).run_sync()

    recording_studio_1 = RecordingStudio(
        {
            RecordingStudio.name: "Abbey Road",
            RecordingStudio.facilities: {
                "restaurant": True,
                "mixing_desk": True,
            },
        }
    )
    recording_studio_1.save().run_sync()

    recording_studio_2 = RecordingStudio(
        {
            RecordingStudio.name: "Electric Lady",
            RecordingStudio.facilities: {
                "restaurant": False,
                "mixing_desk": True,
            },
        },
    )
    recording_studio_2.save().run_sync()

    Album.insert(
        Album(
            {
                Album.name: "Awesome album 1",
                Album.recorded_at: recording_studio_1,
                Album.band: pythonistas,
                Album.release_date: datetime.date(year=2021, month=1, day=1),
            }
        ),
        Album(
            {
                Album.name: "Awesome album 2",
                Album.recorded_at: recording_studio_2,
                Album.band: rustaceans,
                Album.release_date: datetime.date(year=2022, month=2, day=2),
            }
        ),
    ).run_sync()


def run(
    engine: str = "sqlite",
    user: str = "piccolo",
    password: str = "piccolo",
    database: str = "piccolo_playground",
    host: str = "localhost",
    port: int = 5432,
    ipython_profile: bool = False,
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
    :param ipython_profile:
        Set to true to use your own IPython profile. Located at ~/.ipython/.
        For more info see the IPython docs
        https://ipython.readthedocs.io/en/stable/config/intro.html.
    """
    try:
        import IPython
    except ImportError:
        sys.exit(
            "Install iPython using `pip install 'piccolo[playground,sqlite]'` "
            "to use this feature."
        )

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
    else:
        db = SQLiteEngine()
    for _table in TABLES:
        _table._meta._db = db

    print(colored_string("\nTables:\n"))

    for _table in TABLES:
        print(_table._table_str(abbreviated=True))
        print("")

    print(colored_string("Try it as a query builder:"))
    print("await Band.select()")
    print("await Band.select(Band.name)")
    print("await Band.select(Band.name, Band.manager.name)")
    print("\n")

    print(colored_string("Try it as an ORM:"))
    print("b = await Band.objects().where(Band.name == 'Pythonistas').first()")
    print("b.popularity = 10000")
    print("await b.save()")
    print("\n")

    populate()

    from IPython.core.async_helpers import _asyncio_runner

    if ipython_profile:
        print(colored_string("Using your IPython profile\n"))
        # To try this out, set `c.TerminalInteractiveShell.colors = "Linux"`
        # in `~/.ipython/profile_default/ipython_config.py` to set the terminal
        # color.
        conf_args = {}
    else:
        conf_args = {"colors": "neutral"}

    IPython.embed(using=_asyncio_runner, **conf_args)
