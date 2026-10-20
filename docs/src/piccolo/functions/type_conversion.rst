Type conversion functions
=========================

Cast
----

.. currentmodule:: piccolo.query.functions.type_conversion

.. autoclass:: Cast

Notes on databases
------------------

Postgres and CockroachDB have very rich type systems, and you can convert
between most types. SQLite is more limited.

The following query will work in Postgres / Cockroach, but you might get
unexpected results in SQLite, because it doesn't have a native ``TIME`` column
type:

.. code-block:: python

    >>> from piccolo.columns import Time
    >>> from piccolo.query.functions import Cast
    >>> await Concert.select(Cast(Concert.starts, Time()))
