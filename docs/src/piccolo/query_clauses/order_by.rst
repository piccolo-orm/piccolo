.. _order_by:

order_by
========

You can use ``order_by`` clauses with the following queries:

* :ref:`Select`
* :ref:`Objects`

To order the results by a certain column (ascending):

.. code-block:: python

    Band.select().order_by(
        Band.name
    ).run_sync()

To order by descending:

.. code-block:: python

    Band.select().order_by(
        Band.name,
        ascending=False
    ).run_sync()

You can order by multiple columns, and even use joins:

.. code-block:: python

    Band.select().order_by(
        Band.name,
        Band.manager.name
    ).run_sync()
