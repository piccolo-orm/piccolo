import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from piccolo.columns.column_types import Varchar  # noqa: E402
from piccolo.engine.postgres import PostgresEngine  # noqa: E402
from piccolo.table import Table  # noqa: E402

DB = PostgresEngine(config={"database": "piccolo_profile"})


class Band(Table, db=DB):
    name = Varchar()
