.. _Alter:

Alter
=====

This is used to modify an existing table.

.. hint:: It is typically used in conjunction with migrations - see :ref:`Migrations`.

add_column
----------

Used to add a column to an existing table.

.. code-block:: python

        Band.alter().add_column(‘members’, Integer()).run_sync()

drop_column
-----------

Used to drop an existing column.

.. code-block:: python

    Band.alter().drop_column('popularity')

rename_column
-------------

Used to rename an existing column.

.. code-block:: python

    Band.alter().rename_column(Band.popularity, ‘rating’).run_sync()

set_unique
----------

Used to change whether a column is unique or not.

.. code-block:: python

    # To make a row unique:
    Band.alter().set_unique(Band.name, True).run_sync()

    # To stop a row being unique:
    Band.alter().set_unique(Band.name, False).run_sync()
