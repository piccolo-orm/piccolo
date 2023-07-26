Joins
=====

Joins are handled automatically by Piccolo. They work everywhere you'd expect
(select queries, where clauses, etc.).

A `fluent interface <https://en.wikipedia.org/wiki/Fluent_interface>`_  is used,
which lets you traverse foreign keys.

Here's an example of a select query which uses joins (using the
:ref:`example schema <ExampleSchema>`):

.. code-block:: python

    # This gets the band's name, and the manager's name by joining to the
    # manager table:
    >>> await Band.select(Band.name, Band.manager.name)

And a ``where`` clause which uses joins:

.. code-block:: python

    # This automatically joins with the manager table to perform the where
    # clause. It only returns the columns from the band table though by default.
    >>> await Band.select().where(Band.manager.name == 'Guido')

Left joins are used.

join_on
-------

Joins are usually performed using ``ForeignKey`` columns, though there may be
situations where you want to join using a column which isn't a ``ForeignKey``.

You can do this using :meth:`join_on <piccolo.columns.base.Column.join_on>`.

It's generally best to join on unique columns.
