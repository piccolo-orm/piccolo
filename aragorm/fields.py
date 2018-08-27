import typing

from .operators import (
    Equal,
    GreaterEqualThan,
    GreaterThan,
    In,
    LessEqualThan,
    LessThan,
    Like,
    NotEqual,
    NotIn,
    Operator,
)


Iterable = typing.Iterable[typing.Any]


class Field():

    def __init__(self, null: bool = True):
        self.null = null

    def is_in(self, values: Iterable) -> 'Where':
        return Where(field=self, values=values, operator=In)

    def not_in(self, values: Iterable) -> 'Where':
        return Where(field=self, values=values, operator=NotIn)

    def like(self, value: str) -> 'Where':
        if '%' not in value:
            raise ValueError('% is required for like operators')
        return Where(field=self, value=value, operator=Like)

    def format_value(self, value):
        """
        Takes the raw Python value and return a string usable in the database
        query.
        """
        return f'{value}'

    def __lt__(self, value) -> 'Where':
        return Where(field=self, value=value, operator=LessThan)

    def __le__(self, value) -> 'Where':
        return Where(field=self, value=value, operator=LessEqualThan)

    def __gt__(self, value) -> 'Where':
        return Where(field=self, value=value, operator=GreaterThan)

    def __ge__(self, value) -> 'Where':
        return Where(field=self, value=value, operator=GreaterEqualThan)

    def __eq__(self, value) -> 'Where':
        return Where(field=self, value=value, operator=Equal)

    def __ne__(self, value) -> 'Where':
        return Where(field=self, value=value, operator=NotEqual)


class Varchar(Field):
    def __init__(self, length: int = 255, default: str = None, **kwargs):
        self.length = length
        self.default = default
        super().__init__(**kwargs)

    def format_value(self, value):
        if type(value) != str:
            raise ValueError('Varchar only accepts strings')
        # TODO sanitize input
        return f"'{value}'"


class Integer(Field):
    def __init__(self, default: int = None, **kwargs):
        self.default = default
        super().__init__(**kwargs)

###############################################################################

class Combination(object):

    operator = ''

    def __init__(self, first: 'Where', second: 'Where'):
        self.first = first
        self.second = second

    def __str__(self):
        return (
            f'({self.first.__str__()} {self.operator} {self.second.__str__()})'
        )


class And(Combination):
    operator = 'AND'


class Or(Combination):
    operator = 'OR'


class Where(object):

    def __init__(self, field: Field, value: typing.Any = None,
                 values: Iterable = [], operator: Operator = None):
        self.field = field
        self.value = value
        self.values = values
        self.operator = operator

    def __and__(self, value: 'Where') -> And:
        return And(self, value)

    def __or__(self, value: 'Where') -> Or:
        return Or(self, value)

    @property
    def values_str(self):
        return ', '.join(
            [self.field.format_value(v) for v in self.values]
        )

    def __str__(self):
        kwargs = {
            'name': self.field.name
        }
        if self.value:
            kwargs['value'] = self.field.format_value(self.value)
        if self.values:
            kwargs['values'] = self.values_str

        return self.operator.template.format(**kwargs)
