.. _Delete:

Delete
======

This deletes any matching rows from the table.

.. code-block:: python

    >>> await Band.delete().where(Band.name == 'Rustaceans')
    []

-------------------------------------------------------------------------------

force
-----

Piccolo won't let you run a delete query without a where clause, unless you
explicitly tell it to do so. This is to help prevent accidentally deleting all
the data from a table.

.. code-block:: python

    >>> await Band.delete()
    Raises: DeletionError

    # Works fine:
    >>> await Band.delete(force=True)
    []

-------------------------------------------------------------------------------

Query clauses
-------------

returning
~~~~~~~~~

See :ref:`Returning`.

where
~~~~~

See :ref:`Where`
