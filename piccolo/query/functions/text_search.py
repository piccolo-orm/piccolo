"""
Postgres only.

These functions mirror their counterparts in the Postgres docs:

https://www.postgresql.org/docs/current/functions-textsearch.html

Full text search is a Postgres feature - SQLite has its own, unrelated FTS
extension, and CockroachDB's support is incomplete. Passing a column belonging
to a non-Postgres engine into any of these raises a ``ValueError``.

"""

from __future__ import annotations

import re
from typing import Optional, Union

from piccolo.columns.base import Column
from piccolo.custom_types import BasicTypes
from piccolo.querystring import QueryString

TEXT_SEARCH_CONFIG_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def check_engine(*values: Union[Column, QueryString, BasicTypes]) -> None:
    """
    Full text search is Postgres only, so reject columns which belong to any
    other engine.
    """
    for value in values:
        if isinstance(value, Column):
            if value._meta.engine_type != "postgres":
                raise ValueError("Only Postgres supports full text search.")


def get_config_string(config: Optional[str]) -> str:
    """
    The text search configuration is written into the query, rather than being
    passed in as a query parameter.

    Postgres only resolves ``to_tsvector(config, text)`` when the config is a
    constant, and an expression index over it is only ``IMMUTABLE`` because of
    it - so it can't be a parameter.

    As it isn't parameterised, we make sure it's a plain identifier (such as
    ``english``), so it can't be used for SQL injection.

    """
    if config is None:
        return ""

    if not TEXT_SEARCH_CONFIG_PATTERN.match(config):
        raise ValueError(
            "The text search config must be an identifier, for example "
            "'english'."
        )

    return f"'{config}', "


class ToTsVector(QueryString):
    def __init__(
        self,
        document: Union[Column, QueryString, str],
        config: Optional[str] = None,
        alias: Optional[str] = None,
    ):
        """
        Postgres only. Converts text into a ``tsvector`` - the sorted list of
        normalised words which full text search matches against.

        .. code-block:: python

            >>> await Band.select(ToTsVector(Band.name, config='english'))
            [{'to_tsvector': "'pythonista':1"}]

        Most of the time you'll use it with :class:`Matches`, to search:

        .. code-block:: python

            >>> await Band.select(Band.name).where(
            ...     Matches(
            ...         ToTsVector(Band.name, config='english'),
            ...         ToTsQuery('pythonistas', config='english'),
            ...     )
            ... )
            [{'name': 'Pythonistas'}]

        :param document:
            The text to convert - usually a column.
        :param config:
            The text search configuration to use, for example ``'english'``.
            If ``None``, the database's ``default_text_search_config`` is
            used. Note that the single argument form of ``to_tsvector`` is
            ``STABLE`` rather than ``IMMUTABLE``, so it can't be used in an
            expression index - pass a config explicitly if you need one.
        :raises ValueError:
            If the engine isn't Postgres, or the config isn't an identifier.

        """
        check_engine(document)

        super().__init__(
            f"to_tsvector({get_config_string(config)}{{}})",
            document,
            alias=alias or "to_tsvector",
        )


class ToTsQuery(QueryString):
    def __init__(
        self,
        query: Union[Column, QueryString, str],
        config: Optional[str] = None,
        alias: Optional[str] = None,
    ):
        """
        Postgres only. Converts a search query into a ``tsquery``.

        .. code-block:: python

            >>> await Band.select(Band.name).where(
            ...     Matches(
            ...         ToTsVector(Band.name),
            ...         ToTsQuery('python & rust'),
            ...     )
            ... )

        .. warning::
            ``to_tsquery`` expects search operators (``&``, ``|``, ``!``,
            ``<->``, ``:*``), and raises a database error if the input
            contains a stray one. Don't pass unsanitised user input into it -
            use :class:`PlainToTsQuery` or :class:`WebsearchToTsQuery`
            instead, which accept any text.

        :param query:
            The search query, using ``tsquery`` syntax.
        :param config:
            The text search configuration to use, for example ``'english'``.
            If ``None``, the database's ``default_text_search_config`` is
            used.
        :raises ValueError:
            If the engine isn't Postgres, or the config isn't an identifier.

        """
        check_engine(query)

        super().__init__(
            f"to_tsquery({get_config_string(config)}{{}})",
            query,
            alias=alias or "to_tsquery",
        )


class PlainToTsQuery(QueryString):
    def __init__(
        self,
        query: Union[Column, QueryString, str],
        config: Optional[str] = None,
        alias: Optional[str] = None,
    ):
        """
        Postgres only. Converts plain text into a ``tsquery``, with every word
        combined using ``AND``. Unlike :class:`ToTsQuery` it accepts any text,
        so it's safe to use with user input.

        .. code-block:: python

            >>> await Band.select(Band.name).where(
            ...     Matches(
            ...         ToTsVector(Band.name),
            ...         PlainToTsQuery('the pythonistas'),
            ...     )
            ... )
            [{'name': 'Pythonistas'}]

        :param query:
            The text to search for.
        :param config:
            The text search configuration to use, for example ``'english'``.
            If ``None``, the database's ``default_text_search_config`` is
            used.
        :raises ValueError:
            If the engine isn't Postgres, or the config isn't an identifier.

        """
        check_engine(query)

        super().__init__(
            f"plainto_tsquery({get_config_string(config)}{{}})",
            query,
            alias=alias or "plainto_tsquery",
        )


class WebsearchToTsQuery(QueryString):
    def __init__(
        self,
        query: Union[Column, QueryString, str],
        config: Optional[str] = None,
        alias: Optional[str] = None,
    ):
        """
        Postgres only. Converts text into a ``tsquery``, using the syntax
        people expect from a web search engine - quoted phrases, ``or``, and
        ``-`` to exclude. Like :class:`PlainToTsQuery` it accepts any text, so
        it's safe to use with user input.

        .. code-block:: python

            >>> await Band.select(Band.name).where(
            ...     Matches(
            ...         ToTsVector(Band.name),
            ...         WebsearchToTsQuery('"pythonistas" -rustaceans'),
            ...     )
            ... )
            [{'name': 'Pythonistas'}]

        :param query:
            The text to search for.
        :param config:
            The text search configuration to use, for example ``'english'``.
            If ``None``, the database's ``default_text_search_config`` is
            used.
        :raises ValueError:
            If the engine isn't Postgres, or the config isn't an identifier.

        """
        check_engine(query)

        super().__init__(
            f"websearch_to_tsquery({get_config_string(config)}{{}})",
            query,
            alias=alias or "websearch_to_tsquery",
        )


class Matches(QueryString):
    def __init__(
        self,
        document: Union[Column, QueryString],
        query: Union[Column, QueryString],
        alias: Optional[str] = None,
    ):
        """
        Postgres only. The full text search operator (``@@``) - it returns
        ``True`` if the ``tsvector`` matches the ``tsquery``.

        .. code-block:: python

            >>> await Band.select(Band.name).where(
            ...     Matches(
            ...         ToTsVector(Band.name, config='english'),
            ...         PlainToTsQuery('pythonistas', config='english'),
            ...     )
            ... )
            [{'name': 'Pythonistas'}]

        :param document:
            A ``tsvector`` - see :class:`ToTsVector`.
        :param query:
            A ``tsquery`` - see :class:`PlainToTsQuery`,
            :class:`WebsearchToTsQuery` and :class:`ToTsQuery`.
        :raises ValueError:
            If the engine isn't Postgres.

        """
        check_engine(document, query)

        super().__init__("{} @@ {}", document, query, alias=alias)


__all__ = (
    "Matches",
    "PlainToTsQuery",
    "ToTsQuery",
    "ToTsVector",
    "WebsearchToTsQuery",
)
