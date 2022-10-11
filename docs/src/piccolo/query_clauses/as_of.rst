.. _as_of:

as_of
=====

You can use ``as_of`` clause with the following queries:

* :ref:`Select`
* :ref:`Objects`

To retrieve historical data from 5 minutes ago:

.. code-block:: python

    await Band.select().where(
        Band.name == 'Pythonistas'
    ).as_of('-5min')

This generates an ``AS OF SYSTEM TIME`` clause. See `documentation <https://www.cockroachlabs.com/docs/stable/as-of-system-time.html>`_.

This clause accepts a wide variety of time and interval `string formats <https://www.cockroachlabs.com/docs/stable/as-of-system-time.html#using-different-timestamp-formats>`_.

This is very useful for performance, as it will reduce transaction contention across a cluster.

Currently only supported on Cockroach Engine. 
