from __future__ import annotations

import re
from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, Any, Optional, Union

from piccolo.querystring import QueryString, Selectable

if TYPE_CHECKING:
    from piccolo.query.base import Query


_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class CTEError(Exception):
    """
    Raised when a ``CTE`` is malformed, or is used incorrectly.
    """

    pass


def _validate_identifier(value: str, kind: str) -> None:
    if not isinstance(value, str):
        raise CTEError(f"{kind} must be a string.")
    if not _NAME_PATTERN.match(value):
        raise CTEError(f"{kind} {value!r} is not a valid SQL identifier.")


def _count_select_columns(query: Any) -> Optional[int]:
    from piccolo.query.methods.select import Select

    if isinstance(query, Select):
        cols = query.columns_delegate.selected_columns
        if cols:
            return len(cols)
    return None


class CTEColumn(Selectable):
    """
    A column of a ``CTE``, which is rendered as ``"cte_name"."column_name"``.
    Usually created via a :class:`CTERef <piccolo.query.CTERef>`.
    """

    __slots__ = ("cte_name", "column_name")

    def __init__(self, cte_name: str, column_name: str) -> None:
        _validate_identifier(cte_name, "CTE name")
        _validate_identifier(column_name, "CTE column name")
        self.cte_name = cte_name
        self.column_name = column_name
        self._alias = None

    def get_select_string(
        self, engine_type: str, with_alias: bool = True
    ) -> QueryString:
        return QueryString(f'"{self.cte_name}"."{self.column_name}"')

    def __str__(self) -> str:
        return f'"{self.cte_name}"."{self.column_name}"'


class CTERef:
    """
    Describes the columns of a ``CTE``, so they can be referenced in other
    parts of a query. Get one using :meth:`CTE.ref`.
    """

    __slots__ = ("cte_name", "column_names")

    def __init__(self, cte_name: str, column_names: Sequence[str]) -> None:
        _validate_identifier(cte_name, "CTE name")
        if not column_names:
            raise CTEError("CTERef requires at least one column to reference.")
        for cn in column_names:
            _validate_identifier(cn, "CTE column name")
        self.cte_name = cte_name
        self.column_names = tuple(column_names)

    def column(self, name: str) -> CTEColumn:
        """
        Returns the named column. Raises a ``CTEError`` if the CTE doesn't
        declare it.
        """
        if name not in self.column_names:
            raise CTEError(
                f"CTE {self.cte_name!r} has no column {name!r}; "
                f"declared columns: {list(self.column_names)}"
            )
        return CTEColumn(self.cte_name, name)

    def columns(self) -> tuple[CTEColumn, ...]:
        """
        Returns all of the columns, in the order they were declared.
        """
        return tuple(
            CTEColumn(self.cte_name, name) for name in self.column_names
        )

    def __getattr__(self, name: str) -> CTEColumn:
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self.column_names:
            raise AttributeError(
                f"CTE {self.cte_name!r} has no column {name!r}"
            )
        return CTEColumn(self.cte_name, name)

    def __len__(self) -> int:
        return len(self.column_names)

    def __iter__(self) -> Iterator[CTEColumn]:
        for name in self.column_names:
            yield CTEColumn(self.cte_name, name)

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and name in self.column_names

    def from_clause(self) -> QueryString:
        """
        Returns the quoted CTE name, for use in a ``FROM`` clause.
        """
        return QueryString(f'"{self.cte_name}"')

    def select_all(self) -> QueryString:
        """
        Returns a ``SELECT`` query which fetches every column of the CTE.
        """
        cols_sql = ", ".join(
            f'"{self.cte_name}"."{c}"' for c in self.column_names
        )
        return QueryString(f'SELECT {cols_sql} FROM "{self.cte_name}"')


class CTE:
    """
    A Common Table Expression, which can be added to a ``Select``, ``Update``,
    ``Delete`` or ``Insert`` query using ``with_``.

    :param name:
        The name used to refer to the CTE in the rest of the query.
    :param body:
        A query, or a :class:`QueryString <piccolo.querystring.QueryString>`.
    :param recursive_body:
        If provided, this is combined with ``body`` using ``UNION ALL``, to
        make a recursive CTE. It should select from the CTE itself, and
        ``column_names`` must also be provided.
    :param column_names:
        Names for the columns of the CTE. If ``body`` is a ``Select`` query,
        it must select the same number of columns.
    :param materialized:
        ``True`` adds a ``MATERIALIZED`` hint, ``False`` adds
        ``NOT MATERIALIZED``, and ``None`` leaves it up to the database.

    """

    __slots__ = (
        "name",
        "body",
        "recursive_body",
        "column_names",
        "_recursive",
        "_materialized",
    )

    def __init__(
        self,
        name: str,
        body: Union["Query", QueryString],
        recursive_body: Optional[Union["Query", QueryString]] = None,
        column_names: Optional[Sequence[str]] = None,
        materialized: Optional[bool] = None,
    ) -> None:
        _validate_identifier(name, "CTE name")
        if column_names is not None:
            if len(column_names) == 0:
                raise CTEError(
                    "column_names must contain at least one entry, "
                    "or be omitted entirely."
                )
            seen: set[str] = set()
            for cn in column_names:
                _validate_identifier(cn, "CTE column name")
                if cn in seen:
                    raise CTEError(
                        f"duplicate column name {cn!r} in column_names."
                    )
                seen.add(cn)
        if materialized is not None and not isinstance(materialized, bool):
            raise CTEError(
                "materialized must be True, False, or None (default)."
            )
        self.name = name
        self.body = body
        self.recursive_body = recursive_body
        self.column_names = (
            tuple(column_names) if column_names is not None else None
        )
        self._recursive = recursive_body is not None
        self._materialized = materialized
        if self._recursive and column_names is None:
            raise CTEError(
                "A recursive CTE must declare column_names so the "
                "recursive reference is well-typed."
            )
        if column_names is not None:
            body_count = _count_select_columns(body)
            if body_count is not None and body_count != len(column_names):
                raise CTEError(
                    f"CTE {name!r}: body selects {body_count} columns "
                    f"but column_names declares {len(column_names)}."
                )
            if self._recursive:
                rec_count = _count_select_columns(self.recursive_body)
                if rec_count is not None and rec_count != len(column_names):
                    raise CTEError(
                        f"CTE {name!r}: recursive body selects "
                        f"{rec_count} columns but column_names "
                        f"declares {len(column_names)}."
                    )

    @classmethod
    def recursive(
        cls,
        name: str,
        base: Union["Query", QueryString],
        recursive: Union["Query", QueryString],
        column_names: Sequence[str],
        materialized: Optional[bool] = None,
    ) -> "CTE":
        """
        A shortcut for creating a recursive CTE.
        """
        return cls(
            name=name,
            body=base,
            recursive_body=recursive,
            column_names=column_names,
            materialized=materialized,
        )

    @property
    def is_recursive(self) -> bool:
        """
        ``True`` if a ``recursive_body`` was provided.
        """
        return self._recursive

    @property
    def materialized(self) -> Optional[bool]:
        return self._materialized

    def ref(self) -> CTERef:
        """
        Returns a :class:`CTERef <piccolo.query.CTERef>`, which can be used to
        reference the columns of the CTE. ``column_names`` must have been
        provided.
        """
        if self.column_names is None:
            raise CTEError(
                f"CTE {self.name!r} has no declared column_names; "
                "cannot build a reference for unnamed columns."
            )
        return CTERef(self.name, self.column_names)

    def _body_querystring(
        self, body: Union["Query", QueryString]
    ) -> QueryString:
        from piccolo.query.base import Query as _Query

        if isinstance(body, QueryString):
            return body
        if isinstance(body, _Query):
            qss = body.default_querystrings
            if len(qss) != 1:
                raise CTEError(
                    "CTE body must compile to exactly one statement; "
                    f"got {len(qss)}."
                )
            return qss[0]
        raise CTEError(
            "CTE body must be a Query or QueryString instance, got "
            f"{type(body).__name__}."
        )

    def get_inner_querystring(self) -> QueryString:
        """
        Returns the definition of the CTE, as it appears within the ``WITH``
        clause.
        """
        body_qs = self._body_querystring(self.body)
        if self._recursive:
            assert self.recursive_body is not None
            recursive_qs = self._body_querystring(self.recursive_body)
            inner = QueryString(
                "{} UNION ALL {}",
                body_qs,
                recursive_qs,
            )
        else:
            inner = body_qs
        cols = ""
        if self.column_names is not None:
            cols = " (" + ", ".join(f'"{c}"' for c in self.column_names) + ")"
        if self._materialized is None:
            prefix = f'"{self.name}"{cols} AS '
            return QueryString("{}({})", QueryString(prefix), inner)
        materialized_word = (
            "MATERIALIZED" if self._materialized else "NOT MATERIALIZED"
        )
        prefix = f'"{self.name}"{cols} AS {materialized_word} '
        return QueryString("{}({})", QueryString(prefix), inner)


def build_with_clause_querystring(
    ctes: Sequence[CTE],
) -> Optional[QueryString]:
    if not ctes:
        return None
    any_recursive = any(c.is_recursive for c in ctes)
    keyword = "WITH RECURSIVE " if any_recursive else "WITH "
    template_parts = []
    args: list[QueryString] = []
    for index, cte in enumerate(ctes):
        if index > 0:
            template_parts.append(", ")
        template_parts.append("{}")
        args.append(cte.get_inner_querystring())
    template = keyword + "".join(template_parts) + " "
    return QueryString(template, *args)
