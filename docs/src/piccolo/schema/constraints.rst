===========
Constraints
===========

Simple unique constraints
=========================

Unique constraints can be added to a single column using the ``unique=True``
argument of ``Column``:

.. code-block:: python

    class Band(Table):
        name = Varchar(unique=True)

-------------------------------------------------------------------------------

``Table.constraints``
=====================

By adding a ``constraints`` list to your ``Table``, you can implement powerful
``UNIQUE`` and ``CHECK`` constraints.

``Unique``
----------

.. currentmodule:: piccolo.constraints

.. autoclass:: Unique

``Check``
----------

.. autoclass:: Check

How are they created?
---------------------

If creating a new table using ``await MyTable.create_table()``, then the
constraints will also be created.

Also, if using auto migrations, they handle the creation and deletion of these
constraints for you.
