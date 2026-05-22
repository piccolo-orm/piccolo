"""
PostgreSQL full-text search functions.

https://www.postgresql.org/docs/current/functions-textsearch.html

Requires PostgreSQL.
"""

from typing import Optional, Union

from piccolo.columns.base import Column
from piccolo.querystring import QueryString


class ToTsvector(QueryString):
    """
    Converts text to a ``tsvector`` for full-text search indexing.
    """

    def __init__(
        self,
        document: Union[Column, QueryString, str],
        config: Optional[Union[Column, QueryString, str]] = None,
        alias: Optional[str] = "to_tsvector",
    ):
        if config is not None:
            super().__init__(
                "to_tsvector({}, {})", config, document, alias=alias
            )
        else:
            super().__init__("to_tsvector({})", document, alias=alias)


class ToTsquery(QueryString):
    """
    Converts a query string to a ``tsquery``.
    """

    def __init__(
        self,
        query: Union[Column, QueryString, str],
        config: Optional[Union[Column, QueryString, str]] = None,
        alias: Optional[str] = "to_tsquery",
    ):
        if config is not None:
            super().__init__(
                "to_tsquery({}, {})", config, query, alias=alias
            )
        else:
            super().__init__("to_tsquery({})", query, alias=alias)


class PlaintoTsquery(QueryString):
    """
    Converts plain text to a ``tsquery`` (no special operators).
    """

    def __init__(
        self,
        query: Union[Column, QueryString, str],
        config: Optional[Union[Column, QueryString, str]] = None,
        alias: Optional[str] = "plainto_tsquery",
    ):
        if config is not None:
            super().__init__(
                "plainto_tsquery({}, {})", config, query, alias=alias
            )
        else:
            super().__init__("plainto_tsquery({})", query, alias=alias)


class PhrasetoTsquery(QueryString):
    """
    Converts text to a ``tsquery`` matching the exact phrase.
    """

    def __init__(
        self,
        query: Union[Column, QueryString, str],
        config: Optional[Union[Column, QueryString, str]] = None,
        alias: Optional[str] = "phraseto_tsquery",
    ):
        if config is not None:
            super().__init__(
                "phraseto_tsquery({}, {})", config, query, alias=alias
            )
        else:
            super().__init__("phraseto_tsquery({})", query, alias=alias)


class WebsearchToTsquery(QueryString):
    """
    Converts a web-search-style query string to a ``tsquery``.
    """

    def __init__(
        self,
        query: Union[Column, QueryString, str],
        config: Optional[Union[Column, QueryString, str]] = None,
        alias: Optional[str] = "websearch_to_tsquery",
    ):
        if config is not None:
            super().__init__(
                "websearch_to_tsquery({}, {})", config, query, alias=alias
            )
        else:
            super().__init__(
                "websearch_to_tsquery({})", query, alias=alias
            )


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
            super().__init__(
                "ts_rank_cd({}, {})", vector, query, alias=alias
            )


class TsHeadline(QueryString):
    """
    Highlights matching terms in a document for display.
    """

    def __init__(
        self,
        document: Union[Column, QueryString, str],
        query: Union[Column, QueryString, str],
        config: Optional[Union[Column, QueryString, str]] = None,
        options: Optional[str] = None,
        alias: Optional[str] = "ts_headline",
    ):
        if config is not None:
            super().__init__(
                "ts_headline({}, {}, {})",
                config,
                document,
                query,
                alias=alias,
            )
        else:
            super().__init__(
                "ts_headline({}, {})", document, query, alias=alias
            )


__all__ = (
    "PhrasetoTsquery",
    "PlaintoTsquery",
    "ToTsquery",
    "ToTsvector",
    "TsHeadline",
    "TsRank",
    "TsRankCd",
    "WebsearchToTsquery",
)
