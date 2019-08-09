.. _Drop:

Drop
====

This removes a table and all its data from the database.

.. code-block:: python

    >>> Band.drop().run_sync()
    []

.. hint:: It is typically used in conjunction with migrations - see :ref:`Migrations`.
