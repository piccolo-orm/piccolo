from aragorm import model
from aragorm import fields


class Pokemon(model.Model):
    name = fields.Varchar(length=50)
    power = fields.Integer()
