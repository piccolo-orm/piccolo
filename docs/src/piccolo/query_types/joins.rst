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

Improved static typing
----------------------

You can optionally modify the above queries slightly for powerful static typing
support from tools like Mypy and Pylance:

.. code-block:: python

    await Band.select(Band.name, Band.manager._.name)

Notice how we use ``._.`` instead of ``.`` after each foreign key. An easy way
to remember this is ``._.`` looks a bit like a connector in a diagram.

Static type checkers now know that we're referencing the ``name`` column on the
``Manager`` table, which has many advantages:

* Autocompletion of column names.
* Easier code navigation (command + click on column names to navigate to the
  column definition).
* Most importantly, the detection of typos in column names.

This works, no matter how many joins are performed. For example:

.. code-block:: python

    await Concert.select(
        Concert.band_1._.name,
        Concert.band_1._.manager._.name,
    )

.. note:: You may wonder why this syntax is required. We're operating within
    the limits of Python's typing support, which is still fairly young. In the
    future we will hopefully be able to offer identical static typing support
    for ``Band.manager.name`` and ``Band.manager._.name``. But even then,
    the ``._.`` syntax will still be supported.

``join_on``
-----------

Joins are usually performed using ``ForeignKey`` columns, though there may be
situations where you want to join using a column which isn't a ``ForeignKey``.

You can do this using :meth:`join_on <piccolo.columns.base.Column.join_on>`.

It's generally best to join on unique columns.
