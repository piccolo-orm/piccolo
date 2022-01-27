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

You can order by multiple columns, and even use joins:

.. code-block:: python

    await Band.select().order_by(
        Band.name,
        Band.manager.name
    )
