.. _Count:

Count
=====

Returns the number of rows which match the query.

.. code-block:: python

    >>> Band.count().where(Band.name == 'Pythonistas').run_sync()
    1

Query clauses
-------------

where
~~~~~

See :ref:`where`.
