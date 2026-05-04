.. _distinct:

distinct
========

You can use ``distinct`` clauses with the following queries:

* :ref:`Select`

.. code-block:: python

    >>> await Band.select(Band.name).distinct()
    [{'title': 'Pythonistas'}]

This is equivalent to ``SELECT DISTINCT name FROM band`` in SQL.

on
--

Using the ``on`` parameter we can create ``DISTINCT ON`` queries.

.. note:: Postgres and CockroachDB only. For more info, see the `Postgres docs <https://www.postgresql.org/docs/current/sql-select.html#SQL-DISTINCT>`_.

If we have the following table:

.. code-block:: python

    class Album(Table):
        band = Varchar()
        title = Varchar()
        release_date = Date()

With this data in the database:

.. csv-table:: Albums
   :file: ./distinct/albums.csv
   :header-rows: 1

To get the latest album for each band, we can do so with a query like this:

.. code-block:: python

    >>> await Album.select().distinct(
    ...     on=[Album.band]
    ... ).order_by(
    ...     Album.band
    ... ).order_by(
    ...     Album.release_date,
    ...     ascending=False
    ... )

    [
        {
            'id': 2,
            'band': 'Pythonistas',
            'title': 'Py album 2022',
            'release_date': '2022-12-01'
        },
        {
            'id': 4,
            'band': 'Rustaceans',
            'title': 'Rusty album 2022',
            'release_date': '2022-12-01'
        },
    ]

The first column specified in ``on`` must match the first column specified in
``order_by``, otherwise a :class:`DistinctOnError <piccolo.query.mixins.DistinctOnError>` will be raised.

Source
~~~~~~

.. currentmodule:: piccolo.query.mixins

.. autoclass:: DistinctOnError
