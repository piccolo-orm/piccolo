import typing
import dataclasses

from ..operators import (
    Equal,
    GreaterEqualThan,
    GreaterThan,
    In,
    LessEqualThan,
    LessThan,
    Like,
    NotEqual,
    NotIn,
)
from ..types import Iterable
from .combination import Where

if typing.TYPE_CHECKING:
    from ..table import Table


class Column():

    def __init__(
        self,
        null: bool = True,
        primary: bool = False,
        key: bool = False
    ) -> None:
        self.null = null
        self.primary = primary
        self.key = key

    def is_in(self, values: Iterable) -> Where:
        return Where(column=self, values=values, operator=In)

    def not_in(self, values: Iterable) -> Where:
        return Where(column=self, values=values, operator=NotIn)

    def like(self, value: str) -> Where:
        if '%' not in value:
            raise ValueError('% is required for like operators')
        return Where(column=self, value=value, operator=Like)

    def format_value(self, value):
        """
        Takes the raw Python value and return a string usable in the database
        query.
        """
        value = value if value else 'null'
        return f'{value}'

    def __lt__(self, value) -> Where:
        return Where(column=self, value=value, operator=LessThan)

    def __le__(self, value) -> Where:
        return Where(column=self, value=value, operator=LessEqualThan)

    def __gt__(self, value) -> Where:
        return Where(column=self, value=value, operator=GreaterThan)

    def __ge__(self, value) -> Where:
        return Where(column=self, value=value, operator=GreaterEqualThan)

    def __eq__(self, value) -> Where:
        return Where(column=self, value=value, operator=Equal)

    def __ne__(self, value) -> Where:
        return Where(column=self, value=value, operator=NotEqual)

    def __str__(self):
        name = getattr(self, 'name', '')
        column_type = getattr(
            self,
            'column_type',
            self.__class__.__name__.upper()
        )
        query = f'{name} {column_type}'
        if self.primary:
            query += ' PRIMARY'
        if self.key:
            query += ' KEY'
        return query


@dataclasses.dataclass
class Alias():
    """
    Used in 'where' filters, when a table has multiple columns referring to the
    same table via foreign keys.

    Trainer = Alias(User)
    Sponsor = Alias(User)

    class Pokemon():
        trainer = ForeignKey(Trainer)
        sponsor = ForeignKey(Sponsor)

    Pokemon.select().where(
        (Trainer.username == 'ash') &&
        (Sponsor.username == 'professor oak')
    )

    Under the hood it uses the name of the alias to name the joined table.

    For example:

    SELECT
        name,
        trainer.name
    FROM pokemon
    JOIN user AS trainer ON id = trainer.id

    """
    table: typing.Type[Table]
