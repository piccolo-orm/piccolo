===========
Constraints
===========

Single column
=============

Unique constraints can be added to a single column using the ``unique=True``
argument of ``Column``:

.. code-block:: python

    class Band(Table):
        name = Varchar(unique=True)

-------------------------------------------------------------------------------

Multi-column
============

``add_constraints``
-------------------

Use the ``add_constraints`` class method to add multi-column constraints to a
``Table``:

.. currentmodule:: piccolo.table

.. automethod:: Table.add_constraints

-------------------------------------------------------------------------------

Constraint types
================

``UniqueConstraint``
--------------------

.. currentmodule:: piccolo.constraint

.. autoclass:: UniqueConstraint
