import datetime

from ..table import Table
from ..columns import Varchar, Timestamp


class Migration(Table):
    name = Varchar(length=200)
    ran_on = Timestamp(default=datetime.datetime.now)
