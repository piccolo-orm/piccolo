import datetime
import typing

from .base import Column

if typing.TYPE_CHECKING:
    import table  # noqa


class Varchar(Column):

    def __init__(self, length: int = 255, default: str = None,
                 **kwargs) -> None:
        self.length = length
        self.default = default
        super().__init__(**kwargs)

    def format_value(self, value: str):
        if not value:
            return 'null'
        # TODO sanitize input
        return f"'{value}'"


class Integer(Column):

    def __init__(self, default: int = None, **kwargs) -> None:
        self.default = default
        super().__init__(**kwargs)


class Serial(Column):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


class PrimaryKey(Column):

    column_type = 'SERIAL'

    def __init__(self, **kwargs) -> None:
        kwargs.update({
            'primary': True,
            'key': True
        })
        self.default = 'DEFAULT'
        super().__init__(**kwargs)


class Timestamp(Column):

    def __init__(self, default: datetime.datetime = None, **kwargs) -> None:
        self.default = default
        super().__init__(**kwargs)


class Boolean(Column):

    def __init__(self, default: bool = False, **kwargs) -> None:
        self.default = default
        super().__init__(**kwargs)


class ForeignKey(Integer):
    """
    Need to think about how this will work ...

    http://www.postgresqltutorial.com/postgresql-foreign-key/

    some_pokemon.trainer
    >>> 1
    Pokemon.select('name', 'trainer.name')

    I'm not sure  about explicit joins ... only useful if we want to specify
    inner and outer joins.

    Join(Pokemon, User)

    To get the actual User object.

    User.object().where(User.id == some_pokemon.trainer)

    OR

    some_pokemon.related_object('trainer')
    > is just a proxy to the above

    class Pokemon(Table):
        trainer = ForeignKey(User)

    To change the trainer:
    some_pokemon.trainer = some_trainer_id
    some_pokemon.save()
    Or:
    some_pokemon.set_related_object('trainer', some_trainer)

    """

    column_type = 'INTEGER'

    def __init__(self, references: 'table.Table', **kwargs) -> None:
        super().__init__(**kwargs)
        self.references = references
