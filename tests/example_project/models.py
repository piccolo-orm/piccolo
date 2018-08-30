from aragorm import model
from aragorm import columns


class Pokemon(model.Model):
    name = columns.Varchar(length=50)
    trainer = columns.Varchar(length=20)
    power = columns.Integer()
