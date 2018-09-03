from ..table import Table
from ..columns import Varchar


class Migration(Table):
    name = Varchar(length=200)
    # ran_on = Datetime()
