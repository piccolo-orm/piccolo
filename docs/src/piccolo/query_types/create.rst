.. _Create:

Create
======

This creates the table and columns in the database.

.. hint:: You can use migrations instead of manually altering the schema - see :ref:`Migrations`.

.. code-block:: python

    >>> Band.create_table().run_sync()
    []
