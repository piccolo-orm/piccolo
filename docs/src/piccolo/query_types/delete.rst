.. _Delete:

Delete
======

This deletes any matching rows from the table.

.. code-block:: python

    >>> Band.delete().where(Band.name == 'Rustaceans').run_sync()
    []

Query clauses
-------------

where
~~~~~

See :ref:`Where`
