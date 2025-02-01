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

.. _AdvancedConstraints:

Advanced constraints
=====================

You can add you can implement powerful ``UNIQUE`` and ``CHECK`` constraints
on your ``Table``.

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

Mixins
------

Constraints can be added to :ref:`mixin classes <Mixins>` for reusability.
