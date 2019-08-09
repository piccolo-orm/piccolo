.. _order_by:

order_by
========

You can use ``order_by`` clauses with the following queries:

* :ref:`Select`
* :ref:`Objects`

To order the results by a certain column (ascending):

.. code-block:: python

    b = Band
    b.select().order_by(
        b.name
    ).run_sync()

To order by descending:

.. code-block:: python

    b = Band
    b.select().order_by(
        b.name,
        ascending=False
    ).run_sync()

You can order by multiple columns, and even use joins:

.. code-block:: python

    b = Band
    b.select().order_by(
        b.name,
        b.manager.name
    ).run_sync()
