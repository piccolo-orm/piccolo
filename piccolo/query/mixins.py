import dataclasses
import typing as t

from ..columns import And
from ..custom_types import Combinable

if t.TYPE_CHECKING:
    from table import Table  # noqa


class Limit():

    def __init__(self, number: int) -> None:
        if type(number) != int:
            raise TypeError('Limit must be an integer')
        self.number = number

    def __str__(self):
        return f' LIMIT {self.number}'


@dataclasses.dataclass
class OrderBy():
    column_name: str
    ascending: bool

    def __str__(self):
        order = 'ASC' if self.ascending else 'DESC'
        return f' ORDER BY {self.column_name} {order}'


@dataclasses.dataclass
class Output():
    as_json: bool = False
    as_list: bool = False
    as_objects: bool = False


class WhereMixin():

    def __init__(self):
        super().__init__()
        self._where: t.Optional[Combinable] = []

    def where(self, where: Combinable):
        if self._where:
            self._where = And(self._where, where)
        else:
            self._where = where
        return self


class OrderByMixin():

    def __init__(self):
        super().__init__()
        self._order_by: t.Optional[OrderBy] = None

    def order_by(self, column_name: str):
        self._is_valid_column_name(column_name)

        ascending = True
        if column_name.startswith('-'):
            ascending = False
            column_name = column_name[1:]

        self._order_by = OrderBy(column_name, ascending)
        return self


class LimitMixin():

    def __init__(self):
        super().__init__()
        self._limit: t.Optional[Limit] = None

    def limit(self, number: int):
        self._limit = Limit(number)
        return self

    @staticmethod
    def _response_handler(response):
        if len(response) == 0:
            raise ValueError('No results found')

        return response[0]

    def first(self):
        self._limit = Limit(1)
        self.response_handler = self._response_handler
        return self


class DistinctMixin():

    def __init__(self):
        super().__init__()
        self._distinct: bool = False

    def distinct(self):
        self._distinct = True
        return self


class CountMixin():

    def __init__(self):
        super().__init__()
        self._count: bool = False

    def count(self):
        self._count = True
        return self


class AddMixin():

    def __init__(self):
        super().__init__()
        self._add: t.List['Table'] = []

    def add(self, *instances: 'Table'):
        for instance in instances:
            if not isinstance(instance, self.table):
                raise TypeError('Incompatible type added.')
        self._add += instances
        return self


class OutputMixin():
    """
    Example usage:

    .output(as_list=True)
    .output(as_json=True)
    .output(as_json=True, as_list=True)
    """

    def __init__(self):
        super().__init__()
        self._output = Output()

    def output(
        self,
        as_list: t.Optional[bool] = None,
        as_json: t.Optional[bool] = None
    ):
        if type(as_list) is bool:
            self._output.as_list = as_list

        if type(as_json) is bool:
            self._output.as_json = as_json

        return self
