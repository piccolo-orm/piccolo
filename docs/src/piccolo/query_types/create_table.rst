.. _Create:

Create Table
============

This creates the table and columns in the database.

.. hint:: You can use migrations instead of manually altering the schema - see :ref:`Migrations`.

.. code-block:: python

    >>> Band.create_table().run_sync()
    []


To prevent an error from being raised if the table already exists:

.. code-block:: python

    >>> Band.create_table(if_not_exists=True).run_sync()
    []
