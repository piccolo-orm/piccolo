.. _Create:

Create Table
============

This creates the table and columns in the database.

.. hint:: You can use migrations instead of manually altering the schema - see :ref:`Migrations`.

.. code-block:: python

    >>> await Band.create_table()
    []


To prevent an error from being raised if the table already exists:

.. code-block:: python

    >>> await Band.create_table(if_not_exists=True)
    []

create_db_tables / create_db_tables_sync
----------------------------------------

You can create multiple tables at once.

This function will automatically sort tables based on their foreign keys so
they're created in the right order:

.. code-block:: python

    # async version
    >>> from piccolo.table import create_db_tables
    >>> await create_db_tables(Band, Manager, if_not_exists=True)

    # sync version
    >>> from piccolo.table import create_db_tables_sync
    >>> create_db_tables_sync(Band, Manager, if_not_exists=True)
