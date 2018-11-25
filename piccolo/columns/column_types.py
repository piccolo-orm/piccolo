import datetime
import typing as t

from .base import Column

if t.TYPE_CHECKING:
    import table  # noqa
    from ..custom_types import Datetime  # noqa


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

    def __init__(self, default: 'Datetime' = None, **kwargs) -> None:
        self.default = default
        super().__init__(**kwargs)

    def format_value(self, value: t.Optional[datetime.datetime]):
        if not value:
            return 'null'
        dt_string = value.isoformat().replace('T', ' ')
        return f"'{dt_string}'"


class Boolean(Column):

    def __init__(self, default: bool = False, **kwargs) -> None:
        self.default = default
        super().__init__(**kwargs)


class ForeignKey(Integer):
    """
    Need to think about how this will work ...

    http://www.postgresqltutorial.com/postgresql-foreign-key/

    some_band.manager
    >>> 1
    Band.select('name', 'manager.name')

    I'm not sure  about explicit joins ... only useful if we want to specify
    inner and outer joins.

    Join(Band, User)

    To get the actual User object.

    User.object().where(User.id == some_band.manager)

    OR

    some_band.related_object('manager')
    > is just a proxy to the above

    class Band(Table):
        manager = ForeignKey(User)

    To change the manager:
    some_band.manager = some_manager_id
    some_band.save()
    Or:
    some_band.set_related_object('manager', some_manager)

    """

    column_type = 'INTEGER'

    def __init__(self, references: t.Type['table.Table'], **kwargs) -> None:
        super().__init__(**kwargs)
        self.references = references
