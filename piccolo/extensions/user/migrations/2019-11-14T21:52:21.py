from piccolo.columns import Varchar, Boolean
from piccolo.table import Table


ID = "2019-11-14T21:52:21"


class BaseUser(Table, tablename="piccolo_user"):
    username = Varchar(length=100, unique=True)
    password = Varchar(length=255)
    email = Varchar(length=255, unique=True)
    active = Boolean(default=False)
    admin = Boolean(default=False)


async def forwards():
    await BaseUser.create_table().run()


async def backwards():
    await BaseUser.alter().drop_table().run()
