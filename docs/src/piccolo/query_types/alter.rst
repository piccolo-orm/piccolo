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

If you have several tables which you want to drop, you can use ``drop_tables``
instead. It will drop them in the correct order.

.. code-block:: python

    from piccolo.table import drop_tables

    drop_tables(Band, Manager)

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

set_unique
----------

Used to change whether a column is unique or not.

.. code-block:: python

    # To make a row unique:
    await Band.alter().set_unique(Band.name, True)

    # To stop a row being unique:
    await Band.alter().set_unique(Band.name, False)
