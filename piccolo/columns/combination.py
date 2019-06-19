from __future__ import annotations
import typing as t

from .operators import Operator
from ..custom_types import Combinable, Iterable
from piccolo.querystring import QueryString

if t.TYPE_CHECKING:
    from .base import Column  # noqa


class CombinableMixin(object):
    def __and__(self, value: Combinable) -> And:
        return And(self, value)

    def __or__(self, value: Combinable) -> Or:
        return Or(self, value)


class Combination(CombinableMixin):

    operator = ''

    def __init__(self, first: Combinable, second: Combinable) -> None:
        self.first = first
        self.second = second

    @property
    def querystring(self):
        return QueryString(
            '({} ' + self.operator + ' {})',
            self.first.querystring,
            self.second.querystring
        )

    def __str__(self):
        self.querystring.__str__()


class And(Combination):
    operator = 'AND'


class Or(Combination):
    operator = 'OR'


class Where(CombinableMixin):

    def __init__(
        self,
        column: 'Column',
        value: t.Any = None,
        values: Iterable = [],
        operator: t.Type[Operator] = Operator
    ) -> None:
        self.column = column
        self.value = value
        self.values = values
        self.operator = operator

    @property
    def values_querystring(self) -> QueryString:
        template = ', '.join(['{}' for i in self.values])
        return QueryString(
            template,
            *self.values
        )

    @property
    def querystring(self) -> QueryString:
        args: t.List[t.Any] = []
        if self.value:
            args.append(self.value)
        if self.values:
            args.append(self.values_querystring)

        # TODO Want something cleaner than this.
        template = self.operator.template.format(
            name=self.column.get_full_name(just_alias=True),
            value='{}',
            values='{}'
        )

        return QueryString(
            template,
            *args
        )

    def __str__(self):
        return self.querystring.__str__()
