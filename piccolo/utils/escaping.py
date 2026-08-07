from __future__ import annotations

__all__ = ("escape_sql_literal", "quote_ident")


def escape_sql_literal(value: str, delimiter: str = "'") -> str:
    """
    Escape a string so it can be safely embedded within ``delimiter`` in a
    SQL statement.

    This is only needed for DDL statements, where values can't be
    parameterised (for example, the ``DEFAULT`` for a column). Anywhere a
    query can be parameterised, pass the value as an argument to
    :class:`piccolo.querystring.QueryString` instead.

    :param value:
        The string to escape.
    :param delimiter:
        The quoting context the escaped value will be embedded in:

        * ``'`` - a standard SQL string literal, where a single quote is
          escaped by doubling it.
        * ``"`` - an element inside a Postgres array literal, where
          backslashes and double quotes are backslash escaped.
        * ``""`` (empty) - no quoting is applied, so there's nothing to
          escape.

    """
    if delimiter == "'":
        return value.replace("'", "''")
    elif delimiter == '"':
        # Inside a Postgres array literal, elements are double quoted, and
        # backslashes / double quotes are backslash escaped. The backslash
        # must be replaced first, otherwise we'd escape our own escapes.
        return value.replace("\\", "\\\\").replace('"', '\\"')
    else:
        return value


def quote_ident(value: str) -> str:
    """
    Quote a SQL identifier (a table, column, alias, or schema name), so it
    can be safely embedded in a query.

    Identifiers can't be parameterised, so this is how we make sure a name
    can't break out of its quotes and alter the surrounding SQL::

        >>> quote_ident('name')
        '"name"'
        >>> quote_ident('a" , (SELECT 1) AS "b')
        '"a"" , (SELECT 1) AS ""b"'

    :raises ValueError:
        If the identifier contains a NULL byte, which no database engine
        accepts, and which can truncate the statement.

    """
    if "\x00" in value:
        raise ValueError("SQL identifiers can't contain NULL bytes.")

    escaped = value.replace('"', '""')
    return f'"{escaped}"'
