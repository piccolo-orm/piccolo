.. _Create:

Create
======

This creates the table and columns in the database.

.. code-block:: python

    >>> Band.create_table().run_sync()
    []

Alternatively, you can use ``create_table_without_columns``, which just
creates the table, without any columns.

.. code-block:: python

    >>> Band.create_table_without_columns().run_sync()
    []

.. hint:: It is typically used in conjunction with migrations - see :ref:`Migrations`.
