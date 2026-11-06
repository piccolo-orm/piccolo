"""
PostgreSQL full-text search functions.

https://www.postgresql.org/docs/current/functions-textsearch.html

Requires PostgreSQL.
"""

from typing import Optional, Union

from piccolo.columns.base import Column
from piccolo.querystring import QueryString


class _ConfigurableTextSearchFunction(QueryString):
    """
    Base class for text search functions which take an optional
    ``regconfig`` as the first argument - for example
    ``to_tsquery([config,] query)``.
    """

    function_name: str

    def __init__(
        self,
        value: Union[Column, QueryString, str],
        config: Optional[Union[Column, QueryString, str]] = None,
        alias: Optional[str] = None,
    ):
        if alias is None:
            alias = self.function_name

        if config is not None:
            super().__init__(
                f"{self.function_name}({{}}, {{}})",
                config,
                value,
                alias=alias,
            )
        else:
            super().__init__(f"{self.function_name}({{}})", value, alias=alias)


class ToTsvector(_ConfigurableTextSearchFunction):
    """
    Converts text to a ``tsvector`` for full-text search indexing.
    """

    function_name = "to_tsvector"

    def __init__(
        self,
        document: Union[Column, QueryString, str],
        config: Optional[Union[Column, QueryString, str]] = None,
        alias: Optional[str] = "to_tsvector",
    ):
        super().__init__(document, config=config, alias=alias)


class ToTsquery(_ConfigurableTextSearchFunction):
    """
    Converts a query string to a ``tsquery``.
    """

    function_name = "to_tsquery"

    def __init__(
        self,
        query: Union[Column, QueryString, str],
        config: Optional[Union[Column, QueryString, str]] = None,
        alias: Optional[str] = "to_tsquery",
    ):
        super().__init__(query, config=config, alias=alias)


class PlaintoTsquery(_ConfigurableTextSearchFunction):
    """
    Converts plain text to a ``tsquery`` (no special operators).
    """

    function_name = "plainto_tsquery"

    def __init__(
        self,
        query: Union[Column, QueryString, str],
        config: Optional[Union[Column, QueryString, str]] = None,
        alias: Optional[str] = "plainto_tsquery",
    ):
        super().__init__(query, config=config, alias=alias)


class PhrasetoTsquery(_ConfigurableTextSearchFunction):
    """
    Converts text to a ``tsquery`` matching the exact phrase.
    """

    function_name = "phraseto_tsquery"

    def __init__(
        self,
        query: Union[Column, QueryString, str],
        config: Optional[Union[Column, QueryString, str]] = None,
        alias: Optional[str] = "phraseto_tsquery",
    ):
        super().__init__(query, config=config, alias=alias)


class WebsearchToTsquery(_ConfigurableTextSearchFunction):
    """
    Converts a web-search-style query string to a ``tsquery``.
    """

    function_name = "websearch_to_tsquery"

    def __init__(
        self,
        query: Union[Column, QueryString, str],
        config: Optional[Union[Column, QueryString, str]] = None,
        alias: Optional[str] = "websearch_to_tsquery",
    ):
        super().__init__(query, config=config, alias=alias)


class TsRank(QueryString):
    """
    Ranks documents by relevance to a ``tsquery``.

    :param normalization:
        Optional integer controlling rank normalisation behaviour.
        See PostgreSQL docs for values.
    """

    def __init__(
        self,
        vector: Union[Column, QueryString],
        query: Union[Column, QueryString, str],
        normalization: Optional[int] = None,
        alias: Optional[str] = "ts_rank",
    ):
        if normalization is not None:
            super().__init__(
                "ts_rank({}, {}, {})",
                vector,
                query,
                normalization,
                alias=alias,
            )
        else:
            super().__init__("ts_rank({}, {})", vector, query, alias=alias)


class TsRankCd(QueryString):
    """
    Ranks documents by relevance using cover density.

    :param normalization:
        Optional integer controlling rank normalisation behaviour.
    """

    def __init__(
        self,
        vector: Union[Column, QueryString],
        query: Union[Column, QueryString, str],
        normalization: Optional[int] = None,
        alias: Optional[str] = "ts_rank_cd",
    ):
        if normalization is not None:
            super().__init__(
                "ts_rank_cd({}, {}, {})",
                vector,
                query,
                normalization,
                alias=alias,
            )
        else:
            super().__init__("ts_rank_cd({}, {})", vector, query, alias=alias)


class Setweight(QueryString):
    """
    Assigns a weight label ('A', 'B', 'C', or 'D') to a tsvector.

    Used to give different importance to columns when ranking search results.
    """

    def __init__(
        self,
        vector: Union[Column, QueryString],
        weight: str,
        alias: Optional[str] = "setweight",
    ):
        super().__init__("setweight({}, {})", vector, weight, alias=alias)


class TsHeadline(QueryString):
    """
    Highlights matching terms in a document for display.

    :param options:
        Optional string of ``ts_headline`` options - for example
        ``'StartSel=<b>, StopSel=</b>, MaxWords=20'``.

    """

    def __init__(
        self,
        document: Union[Column, QueryString, str],
        query: Union[Column, QueryString, str],
        config: Optional[Union[Column, QueryString, str]] = None,
        options: Optional[str] = None,
        alias: Optional[str] = "ts_headline",
    ):
        args: list[Union[Column, QueryString, str]] = []
        if config is not None:
            args.append(config)
        args += [document, query]
        if options is not None:
            args.append(options)

        placeholders = ", ".join("{}" for _ in args)
        super().__init__(f"ts_headline({placeholders})", *args, alias=alias)


__all__ = (
    "PhrasetoTsquery",
    "PlaintoTsquery",
    "Setweight",
    "ToTsquery",
    "ToTsvector",
    "TsHeadline",
    "TsRank",
    "TsRankCd",
    "WebsearchToTsquery",
)
