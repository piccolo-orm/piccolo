.. _Alter:

Alter
=====

This is used to modify an existing table.

.. hint:: You can use migrations instead of manually altering the schema - see :ref:`Migrations`.

-------------------------------------------------------------------------------

add_column
----------

Used to add a column to an existing table.

.. code-block:: python

    await Band.alter().add_column('members', Integer())

-------------------------------------------------------------------------------

drop_column
-----------

Used to drop an existing column.

.. code-block:: python

    await Band.alter().drop_column('popularity')

-------------------------------------------------------------------------------

drop_table
----------

Used to drop the table - use with caution!

.. code-block:: python

    await Band.alter().drop_table()

drop_db_tables / drop_db_tables_sync
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have several tables which you want to drop, you can use
:func:`drop_db_tables <piccolo.table.drop_db_tables>` or
:func:`drop_db_tables_sync <piccolo.table.drop_db_tables_sync>`. The tables
will be dropped in the correct order based on their foreign keys.

.. code-block:: python

    # async version
    >>> from piccolo.table import drop_db_tables
    >>> await drop_db_tables(Band, Manager)

    # sync version
    >>> from piccolo.table import drop_db_tables_sync
    >>> drop_db_tables_sync(Band, Manager)

-------------------------------------------------------------------------------

rename_column
-------------

Used to rename an existing column.

.. code-block:: python

    await Band.alter().rename_column(Band.popularity, 'rating')

-------------------------------------------------------------------------------

set_null
--------

Set whether a column is nullable or not.

.. code-block:: python

    # To make a row nullable:
    await Band.alter().set_null(Band.name, True)

    # To stop a row being nullable:
    await Band.alter().set_null(Band.name, False)

-------------------------------------------------------------------------------

set_schema
----------

Used to change the `schema <https://www.postgresql.org/docs/current/ddl-schemas.html>`_
which a table lives in.

.. code-block:: python

    await Band.alter().set_schema('schema1')

.. note:: Schemas are a way of organising the tables within a database. Only
    Postgres and Cockroach support schemas.

-------------------------------------------------------------------------------

set_unique
----------

Used to change whether a column is unique or not.

.. code-block:: python

    # To make a row unique:
    await Band.alter().set_unique(Band.name, True)

    # To stop a row being unique:
    await Band.alter().set_unique(Band.name, False)
