import typing
import uuid

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
        self.uuid = uuid.uuid4()

    def __hash__(self):
        return hash(self.uuid)

    def is_in(self, values: Iterable) -> 'Where':
        return Where(field=self, values=values, operator=In)

    def not_in(self, values: Iterable) -> 'Where':
        return Where(field=self, values=values, operator=NotIn)

    def like(self, value: str) -> 'Where':
        if '%' not in value:
            raise ValueError('% is required for like operators')
        return Where(field=self, value=value, operator=Like)

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


class Integer(Field):
    def __init__(self, default: int = None, **kwargs):
        self.default = default
        super().__init__(**kwargs)

###############################################################################

class Combination(object):
    def __init__(self, first: 'Where', second: 'Where'):
        self.first = first
        self.second = second


class And(Combination):
    pass


class Or(Combination):
    pass


class Where(object):
    """
    Can potentially simplify things dramatically here by just accepting
    postgres where clauses directly, avoiding the need for equal, greater than
    etc syntax.
    """

    def __init__(self, field: Field, value: typing.Any = None,
                 values: Iterable = [], operator: Operator = None):
        self.field = field
        self.value = value
        self.values = values
        self.operator = operator

    def __and__(self, value: 'Where') -> And:
        """
        This is a challenge now ... I think I just have WhereAnd, and WhereOr.
        """
        return And(self, value)

    def __or__(self, value: 'Where') -> Or:
        """
        This is a challenge now ... I think I just have WhereAnd, and WhereOr.
        """
        return And(self, value)

    @property
    def values_str(self):
        return ', '.join([str(v) for v in self.values])

    def get_sql(self, name: str):
        return self.operator.template.format(
            name=name,
            value=self.value,
            values=self.values_str,
        )

    def __str__():
        return self.operator.template
