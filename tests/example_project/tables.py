from aragorm import table
from aragorm import columns


DB = {
    'host': 'localhost',
    'database': 'aragorm',
    'user': 'aragorm',
    'password': 'aragorm'
}


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


class Stadium(table.Table):
    pass


# Need Alias already ...
# will live where???
# what does Alias even do???
# lives in column ...
class Battle(table.Table):
    pass
