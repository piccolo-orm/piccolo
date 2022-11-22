.. _order_by:

order_by
========

You can use ``order_by`` clauses with the following queries:

* :ref:`Select`
* :ref:`Objects`

To order the results by a certain column (ascending):

.. code-block:: python

    await Band.select().order_by(
        Band.name
    )

To order by descending:

.. code-block:: python

    await Band.select().order_by(
        Band.name,
        ascending=False
    )

You can specify the column name as a string if you prefer:

.. code-block:: python

    await Band.select().order_by(
        'name'
    )

You can order by multiple columns, and even use joins:

.. code-block:: python

    await Band.select().order_by(
        Band.name,
        Band.manager.name
    )

-------------------------------------------------------------------------------

Advanced
--------

Ascending and descending
~~~~~~~~~~~~~~~~~~~~~~~~

If you want to order by multiple columns, with some ascending, and some
descending, then you can do so using multiple ``order_by`` statements:


.. code-block:: python

    await Band.select().order_by(
        Band.name,
    ).order_by(
        Band.popularity,
        ascending=False
    )

``OrderByRaw``
~~~~~~~~~~~~~~

SQL's ``ORDER BY`` clause is surprisingly rich in functionality, and there may
be situations where you want to specify the ``ORDER BY`` explicitly using SQL.
To do this use ``OrderByRaw``.

In the example below, we are ordering the results randomly:

.. code-block:: python

    from piccolo.query import OrderByRaw

    await Band.select(Band.name).order_by(
        OrderByRaw('random()'),
    )

The above is equivalent to the following SQL:

.. code-block:: sql

    SELECT "band"."name" FROM band ORDER BY random() ASC
