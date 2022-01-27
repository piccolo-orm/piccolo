.. _distinct:

distinct
========

You can use ``distinct`` clauses with the following queries:

* :ref:`Select`

.. code-block:: python

    >>> await Band.select(Band.name).distinct()
    [{'title': 'Pythonistas'}]

This is equivalent to ``SELECT DISTINCT name FROM band`` in SQL.
