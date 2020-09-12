.. _group_by:

group_by
========

You can use ``group_by`` clauses with the following queries:

* :ref:`Select`

It is used in combination with aggregate functions - ``Count`` is currently
supported.

Count
-----

In the following query, we get a count of the number of bands per manager:

.. code-block:: python

    >>> from piccolo.query.methods.select import Count

    >>> b = Band
    >>> b.select(
    >>>     b.manager.name,
    >>>     Count(b.manager)
    >>> ).group_by(
    >>>     b.manager
    >>> ).run_sync()

    [
        {"manager.name": "Graydon", "count": 1},
        {"manager.name": "Guido", "count": 1}
    ]

.. currentmodule:: piccolo.query.methods.select

.. autoclass:: Count
