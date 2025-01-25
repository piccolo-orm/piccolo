===========
Constraints
===========

Unique constraints
==================

Single column
-------------

Unique constraints can be added to a single column using the ``unique=True``
argument of ``Column``:

.. code-block:: python

    class Band(Table):
        name = Varchar(unique=True)

Multi-column
------------

Use the ``add_unique_constraint`` method to add a multi-column constraint to a
``Table``:

.. currentmodule:: piccolo.table

.. automethod:: Table.add_unique_constraint

-------------------------------------------------------------------------------

Check constraints
=================

.. automethod:: Table.add_check_constraint
