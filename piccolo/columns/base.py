import typing as t
import warnings

from .operators import (
    Equal,
    GreaterEqualThan,
    GreaterThan,
    In,
    LessEqualThan,
    LessThan,
    Like,
    ILike,
    NotEqual,
    NotIn,
    NotLike,
    Operator
)
from .combination import Where
from ..custom_types import Iterable
from ..querystring import QueryString

if t.TYPE_CHECKING:
    from ..table import Table  # noqa
    from .column_types import ForeignKey  # noqa


class Column():

    value_type: t.Type = int

    def __init__(
        self,
        null: bool = True,
        primary: bool = False,
        key: bool = False
    ) -> None:
        self.null = null
        self.primary = primary
        self.key = key
        # Set by Table metaclass:
        self._name: t.Optional[str] = None
        # Used by foreign keys:
        self.call_chain: t.List['ForeignKey'] = []
        self.table_alias: t.Optional[str] = None

    def is_in(self, values: Iterable) -> Where:
        return Where(column=self, values=values, operator=In)

    def not_in(self, values: Iterable) -> Where:
        return Where(column=self, values=values, operator=NotIn)

    def like(self, value: str) -> Where:
        if '%' not in value:
            raise ValueError('% is required for like operators')
        return Where(column=self, value=value, operator=Like)

    def ilike(self, value: str) -> Where:
        if '%' not in value:
            raise ValueError('% is required for ilike operators')
        if self._table.Meta.db.engine_type == 'postgres':
            operator: t.Type[Operator] = ILike
        else:
            warnings.warn(
                "SQLite doesn't support ILIKE currently, falling back to LIKE."
            )
            operator = Like
        return Where(column=self, value=value, operator=operator)

    def not_like(self, value: str) -> Where:
        if '%' not in value:
            raise ValueError('% is required for like operators')
        return Where(column=self, value=value, operator=NotLike)

    def __lt__(self, value) -> Where:
        return Where(column=self, value=value, operator=LessThan)

    def __le__(self, value) -> Where:
        return Where(column=self, value=value, operator=LessEqualThan)

    def __gt__(self, value) -> Where:
        return Where(column=self, value=value, operator=GreaterThan)

    def __ge__(self, value) -> Where:
        return Where(column=self, value=value, operator=GreaterEqualThan)

    def __eq__(self, value) -> Where:  # type: ignore
        return Where(column=self, value=value, operator=Equal)

    def __ne__(self, value) -> Where:  # type: ignore
        return Where(column=self, value=value, operator=NotEqual)

    def __hash__(self):
        return hash(self._name)

    def get_full_name(self, just_alias=False) -> str:
        """
        Returns the full column name, taking into account joins.
        """
        column_name = self._name

        if not self.call_chain:
            return f"{self._table.Meta.tablename}.{column_name}"

        column_name = (
            "$".join([i._name for i in self.call_chain])
            + f"${column_name}"
        )
        alias = f"{self.call_chain[-1].table_alias}.{self._name}"
        if just_alias:
            return alias
        else:
            return f'{alias} AS "{column_name}"'

    @property
    def querystring(self) -> QueryString:
        """
        Used when creating tables.
        """
        name = getattr(self, '_name', '')
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

        references = getattr(self, 'references', None)
        if references:
            query += f' REFERENCES {references.Meta.tablename}'

        return QueryString(query)

    def __str__(self):
        return self.querystring.__str__()
