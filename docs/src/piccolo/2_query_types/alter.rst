.. _Alter:

Alter
=====

This is used to modify an existing table.

.. hint:: It is typically used in conjunction with migrations - see :ref:`Migrations`.

add
---

Used to add a column to an existing table.

.. code-block:: python

        Band.alter().add(‘members’, Integer()).run_sync()

drop
----

Used to drop an existing column.

.. code-block:: python

    Band.alter().drop('popularity')

rename
------

Used to rename an existing column.

.. code-block:: python

        Band.alter().rename(Band.popularity, ‘rating’).run_sync()
