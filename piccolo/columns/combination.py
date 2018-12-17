import typing

from .operators import Operator
from ..custom_types import Combinable, Iterable

if typing.TYPE_CHECKING:
    from .base import Column  # noqa


class CombinableMixin(object):
    def __and__(self, value: Combinable) -> 'And':
        return And(self, value)

    def __or__(self, value: Combinable) -> 'Or':
        return Or(self, value)


class Combination(CombinableMixin):

    operator = ''

    def __init__(self, first: Combinable, second: Combinable) -> None:
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


class Where(CombinableMixin):

    def __init__(
        self,
        column: 'Column',
        value: typing.Any = None,
        values: Iterable = [],
        operator: typing.Type[Operator] = None
    ) -> None:
        self.column = column
        self.value = value
        self.values = values
        self.operator = operator

    @property
    def values_str(self) -> str:
        return ', '.join(
            [self.column.format_value(v) for v in self.values]
        )

    def __str__(self):
        kwargs = {
            'name': self.column._name
        }
        if self.value:
            kwargs['value'] = self.column.format_value(self.value)
        if self.values:
            kwargs['values'] = self.values_str

        return self.operator.template.format(**kwargs)
