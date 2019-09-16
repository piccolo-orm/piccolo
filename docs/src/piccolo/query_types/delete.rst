.. _Delete:

Delete
======

This deletes any matching rows from the table.

.. code-block:: python

    >>> Band.delete().where(Band.name == 'Rustaceans').run_sync()
    []

force
-----

Piccolo won't let you run a delete query without a where clause, unless you
explicitly tell it to do so. This is to help prevent accidentally deleting all
the data from a table.

.. code-block:: python

    >>> Band.delete().run_sync()
    Raises: DeletionError

    # Works fine:
    >>> Band.delete(force=True).run_sync()
    []

Query clauses
-------------

where
~~~~~

See :ref:`Where`
