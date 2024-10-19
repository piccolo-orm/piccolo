from __future__ import annotations

import typing as t
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from importlib.util import find_spec
from string import Formatter

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.table import Table
    from piccolo.columns import Column

from uuid import UUID

if find_spec("asyncpg"):
    from asyncpg.pgproto.pgproto import UUID as apgUUID
else:
    apgUUID = UUID


class Selectable(metaclass=ABCMeta):
    """
    Anything which inherits from this can be used in a select query.
    """

    __slots__ = ("_alias",)

    _alias: t.Optional[str]

    @abstractmethod
    def get_select_string(
        self, engine_type: str, with_alias: bool = True
    ) -> QueryString:
        """
        In a query, what to output after the select statement - could be a
        column name, a sub query, a function etc. For a column it will be the
        column name.
        """
        raise NotImplementedError()

    def as_alias(self, alias: str) -> Selectable:
        """
        Allows column names to be changed in the result of a select.
        """
        self._alias = alias
        return self


@dataclass
class Fragment:
    prefix: str
    index: int = 0
    no_arg: bool = False


class QueryString(Selectable):
    """
    When we're composing complex queries, we're combining QueryStrings, rather
    than concatenating strings directly. The reason for this is QueryStrings
    keep the parameters separate, so we can pass parameterised queries to the
    engine - which helps prevent SQL Injection attacks.
    """

    __slots__ = (
        "template",
        "args",
        "query_type",
        "table",
        "_frozen_compiled_strings",
        "columns",
    )

    def __init__(
        self,
        template: str,
        *args: t.Any,
        query_type: str = "generic",
        table: t.Optional[t.Type[Table]] = None,
        alias: t.Optional[str] = None,
    ) -> None:
        """
        :param template:
            The SQL query, with curly brackets as placeholders for any values::

                "WHERE {} = {}"

        :param args:
            The values to insert (one value is needed for each set of curly
            braces in the template).
        :param query_type:
            The query type is sometimes used by the engine to modify how the
            query is run. For example, INSERT queries on old SQLite versions.
        :param table:
            Sometimes the ``piccolo.engine.base.Engine`` needs access to the
            table that the query is being run on.

        """
        self.template = template
        self.query_type = query_type
        self.table = table
        self._frozen_compiled_strings: t.Optional[
            t.Tuple[str, t.List[t.Any]]
        ] = None
        self._alias = alias
        self.args, self.columns = self.process_args(args)

    def process_args(
        self, args: t.Sequence[t.Any]
    ) -> t.Tuple[t.Sequence[t.Any], t.Sequence[Column]]:
        """
        If a Column is passed in, we convert it to the name of the column
        (including joins).
        """
        from piccolo.columns import Column

        processed_args = []
        columns = []

        for arg in args:
            if isinstance(arg, Column):
                columns.append(arg)
                arg = QueryString(
                    f"{arg._meta.get_full_name(with_alias=False)}"
                )
            elif isinstance(arg, QueryString):
                columns.extend(arg.columns)

            processed_args.append(arg)

        return (processed_args, columns)

    def as_alias(self, alias: str) -> QueryString:
        self._alias = alias
        return self

    def __str__(self):
        """
        The SQL returned by the ``__str__`` method isn't used directly in
        queries - it's just a usability feature.
        """
        _, bundled, combined_args = self.bundle(
            start_index=1, bundled=[], combined_args=[]
        )
        template = "".join(
            fragment.prefix + ("" if fragment.no_arg else "{}")
            for fragment in bundled
        )

        # Do some basic type conversion here.
        converted_args = []
        for arg in combined_args:
            _type = type(arg)
            if _type == str:
                converted_args.append(f"'{arg}'")
            elif _type == datetime:
                dt_string = arg.isoformat()
                converted_args.append(f"'{dt_string}'")
            elif _type == UUID or _type == apgUUID:
                converted_args.append(f"'{arg}'")
            elif arg is None:
                converted_args.append("null")
            else:
                converted_args.append(arg)

        return template.format(*converted_args)

    def bundle(
        self,
        start_index: int = 1,
        bundled: t.Optional[t.List[Fragment]] = None,
        combined_args: t.Optional[t.List] = None,
    ):
        # Split up the string, separating by {}.
        fragments = [
            Fragment(prefix=i[0]) for i in Formatter().parse(self.template)
        ]

        bundled = [] if bundled is None else bundled
        combined_args = [] if combined_args is None else combined_args

        for index, fragment in enumerate(fragments):
            try:
                value = self.args[index]
            except IndexError:
                # trailing element
                fragment.no_arg = True
                bundled.append(fragment)
            else:
                if isinstance(value, QueryString):
                    fragment.no_arg = True
                    bundled.append(fragment)

                    start_index, _, _ = value.bundle(
                        start_index=start_index,
                        bundled=bundled,
                        combined_args=combined_args,
                    )
                else:
                    fragment.index = start_index
                    bundled.append(fragment)
                    start_index += 1
                    combined_args.append(value)

        return (start_index, bundled, combined_args)

    def compile_string(
        self, engine_type: str = "postgres"
    ) -> t.Tuple[str, t.List[t.Any]]:
        """
        Compiles the template ready for the engine - keeping the arguments
        separate from the template.
        """
        if self._frozen_compiled_strings is not None:
            return self._frozen_compiled_strings

        _, bundled, combined_args = self.bundle(
            start_index=1, bundled=[], combined_args=[]
        )
        if engine_type in ("postgres", "cockroach"):
            string = "".join(
                fragment.prefix
                + ("" if fragment.no_arg else f"${fragment.index}")
                for fragment in bundled
            )

        elif engine_type == "sqlite":
            string = "".join(
                fragment.prefix + ("" if fragment.no_arg else "?")
                for fragment in bundled
            )

        else:
            raise Exception("Engine type not recognised")

        return (string, combined_args)

    def freeze(self, engine_type: str = "postgres"):
        self._frozen_compiled_strings = self.compile_string(
            engine_type=engine_type
        )

    ###########################################################################

    def get_select_string(
        self, engine_type: str, with_alias: bool = True
    ) -> QueryString:
        if with_alias and self._alias:
            return QueryString("{} AS " + f'"{self._alias}"', self)
        else:
            return self

    def get_where_string(self, engine_type: str) -> QueryString:
        return self.get_select_string(
            engine_type=engine_type, with_alias=False
        )

    ###########################################################################
    # Basic logic

    def __eq__(self, value) -> QueryString:  # type: ignore[override]
        if value is None:
            return QueryString("{} IS NULL", self)
        else:
            return QueryString("{} = {}", self, value)

    def __ne__(self, value) -> QueryString:  # type: ignore[override]
        if value is None:
            return QueryString("{} IS NOT NULL", self, value)
        else:
            return QueryString("{} != {}", self, value)

    def eq(self, value) -> QueryString:
        return self.__eq__(value)

    def ne(self, value) -> QueryString:
        return self.__ne__(value)

    def __add__(self, value) -> QueryString:
        return QueryString("{} + {}", self, value)

    def __sub__(self, value) -> QueryString:
        return QueryString("{} - {}", self, value)

    def __gt__(self, value) -> QueryString:
        return QueryString("{} > {}", self, value)

    def __ge__(self, value) -> QueryString:
        return QueryString("{} >= {}", self, value)

    def __lt__(self, value) -> QueryString:
        return QueryString("{} < {}", self, value)

    def __le__(self, value) -> QueryString:
        return QueryString("{} <= {}", self, value)

    def __truediv__(self, value) -> QueryString:
        return QueryString("{} / {}", self, value)

    def __mul__(self, value) -> QueryString:
        return QueryString("{} * {}", self, value)

    def __pow__(self, value) -> QueryString:
        return QueryString("{} ^ {}", self, value)

    def __mod__(self, value) -> QueryString:
        return QueryString("{} % {}", self, value)

    def is_in(self, value) -> QueryString:
        return QueryString("{} IN {}", self, value)

    def not_in(self, value) -> QueryString:
        return QueryString("{} NOT IN {}", self, value)

    def like(self, value: str) -> QueryString:
        return QueryString("{} LIKE {}", self, value)

    def ilike(self, value: str) -> QueryString:
        return QueryString("{} ILIKE {}", self, value)


class Unquoted(QueryString):
    """
    This is deprecated - just use QueryString directly.
    """

    pass
