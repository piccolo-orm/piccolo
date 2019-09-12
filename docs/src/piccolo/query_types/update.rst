.. _Update:

Update
======

This is used to update any rows in the table which match the criteria.

.. code-block:: python

    >>> Band.update().values({
    >>>     Band.name: 'Pythonistas 2'
    >>> }).where(
    >>>     Band.name == 'Pythonistas'
    >>> ).run_sync()
    []

Query clauses
-------------

where
~~~~~

See :ref:`Where`.
