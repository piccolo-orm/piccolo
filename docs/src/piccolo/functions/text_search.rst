Text search functions
=====================

.. currentmodule:: piccolo.query.functions.text_search

.. note:: Postgres only. SQLite has its own, unrelated FTS extension, and
    CockroachDB's support is incomplete. Passing a column belonging to any
    other engine into these functions raises a ``ValueError``.

Postgres full text search works in two steps - the text being searched is
converted into a ``tsvector``, the search terms are converted into a
``tsquery``, and the two are compared with the ``@@`` operator.

.. code-block:: python

    from piccolo.query.functions import (
        Matches,
        ToTsVector,
        WebsearchToTsQuery,
    )

    await Band.select(Band.name).where(
        Matches(
            ToTsVector(Band.name, config='english'),
            WebsearchToTsQuery('pythonistas', config='english'),
        )
    )

ToTsVector
----------

.. autoclass:: ToTsVector

ToTsQuery
---------

.. autoclass:: ToTsQuery

PlainToTsQuery
--------------

.. autoclass:: PlainToTsQuery

WebsearchToTsQuery
------------------

.. autoclass:: WebsearchToTsQuery

Matches
-------

.. autoclass:: Matches
