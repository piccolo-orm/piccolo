.. _Alter:

Alter
=====

This is used to modify an existing table.

.. hint:: You can use migrations instead of manually altering the schema - see :ref:`Migrations`.


add_column
----------

Used to add a column to an existing table.

.. code-block:: python

    Band.alter().add_column('members', Integer()).run_sync()


drop_column
-----------

Used to drop an existing column.

.. code-block:: python

    Band.alter().drop_column('popularity').run_sync()


drop_table
----------

Used to drop the table - use with caution!

.. code-block:: python

    Band.alter().drop_table().run_sync()

If you have several tables which you want to drop, you can use ``drop_tables``
instead. It will drop them in the correct order.

.. code-block:: python

    from piccolo.table import drop_tables

    drop_tables(Band, Manager)

rename_column
-------------

Used to rename an existing column.

.. code-block:: python

    Band.alter().rename_column(Band.popularity, 'rating').run_sync()


set_null
--------

Set whether a column is nullable or not.

.. code-block:: python

    # To make a row nullable:
    Band.alter().set_null(Band.name, True).run_sync()

    # To stop a row being nullable:
    Band.alter().set_null(Band.name, False).run_sync()


set_unique
----------

Used to change whether a column is unique or not.

.. code-block:: python

    # To make a row unique:
    Band.alter().set_unique(Band.name, True).run_sync()

    # To stop a row being unique:
    Band.alter().set_unique(Band.name, False).run_sync()
