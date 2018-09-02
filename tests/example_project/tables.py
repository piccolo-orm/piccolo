from aragorm import table
from aragorm import columns


class Pokemon(table.Table):
    name = columns.Varchar(length=50)
    trainer = columns.Varchar(length=20)
    power = columns.Integer()
